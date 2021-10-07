from flask_login.utils import login_required, current_user
from EcommerceStore import db
from flask import g, render_template, url_for, redirect, flash, abort, request, send_from_directory, Blueprint
from EcommerceStore.models import (SoldProducts, Cart, BuyerCart, Product, User, Category)
from EcommerceStore.utils import UtilityFunctions
from datetime import timedelta, datetime


carts = Blueprint("carts", __name__)

@carts.route("/product/<int:product_id>/cart", methods=["GET", "POST"])
@login_required
def add_to_cart(product_id):
    product = Product.query.filter_by(id=product_id).first_or_404()
    if current_user.role == 'seller' and product.seller_products[0].seller == current_user:
        flash("You can not purchases your own product!", "info")
        return redirect(url_for("main.home"))
    buyer = User.query.get(current_user.id)
    if not buyer:
        return abort(404)

    cart = Cart.query.filter_by(buyer_id=buyer.id).first()
    # Checking if the cart exists
    if cart is None:
        # First Creating the cart
        cart = Cart(buyer_id=buyer.id)
        db.session.add(cart)
        db.session.commit()
        # Then adding respective products in the cart
        bc = BuyerCart(cart_id=cart.id, product_id=product.id, quantity=1)
        db.session.add(bc)
        db.session.commit()
    else:
        bc = BuyerCart.query.filter_by(cart_id=cart.id, product_id=product.id).first()
        if bc is None:
            # check if the product already exists
            bc = BuyerCart(cart_id=cart.id, product_id=product.id, quantity=1)
            db.session.add(bc)
            db.session.commit()
        else:
            # Just incrementing the quantity if the prouct is already there in the cart
            bc.quantity += 1

    db.session.commit()
    return redirect(url_for('carts.cart_show', cart_id=cart.id, user_id=current_user.id))


@carts.route("/cart", methods=["GET", "POST"])
@login_required
def cart():
    '''
    Creates the cart object in the database if it does not exist.
    '''
    user_id = current_user.id
    cart = Cart.query.filter_by(buyer_id=user_id).first()
    if cart is None:
        cart = Cart(buyer_id=user_id)
        db.session.add(cart)
        db.session.commit()
    return redirect(url_for("carts.cart_show", cart_id=cart.id, user_id=user_id))

@carts.route("/cart/<int:cart_id>/<int:user_id>", methods=["GET","POST"])
@login_required
def cart_show(cart_id, user_id):
    # Checking if the user is trying to access only his cart
    if current_user.id != user_id:
        return abort(403)

    cart = Cart.query.get(cart_id)
    # Checks if the cart exists.
    if cart is None:
        return abort(404)

    # If the cart does not belong to the user trying to access then returns 403 error.
    if cart.buyer.id != user_id:
        return abort(403)
    
    if request.method == 'GET':
        if request.args.get('quantity'):
            # Fetches quantity_list url parameter
            quantity_list = request.args.getlist("quantity")
            return redirect(url_for("carts.generate_bill", cart_id=cart_id, user_id=user_id, quantity_list=quantity_list))
    return render_template("cart.html", title="Cart", cart=cart)

@carts.route("/cart/<int:cart_id>/<int:user_id>/<int:product_id>", methods=["GET","POST"])
@login_required
def remove_product_cart(cart_id, user_id, product_id):
    if current_user.id != user_id:
        return abort(403)

    cart = Cart.query.get(cart_id)
    if cart is None:
        return abort(404)

    if cart.buyer.id != user_id:
        return abort(403)

    buyer_cart = BuyerCart.query.filter_by(cart_id=cart_id, product_id=product_id).first()
    if buyer_cart is not None:
        db.session.delete(buyer_cart)
        db.session.commit()

    return redirect(url_for("carts.cart_show",cart_id=cart_id, user_id=user_id))

@carts.route("/generate_bill/cart/<int:cart_id>/<int:user_id>/quantity<string:quantity_list>", methods=["GET", "POST"])
@login_required
def generate_bill(cart_id, user_id, quantity_list=None):
    '''
    Generates the bill of the individual product.
    '''
    if current_user.id != user_id:
        return abort(403)

    cart = Cart.query.get(cart_id)
    if cart is None:
        return abort(404)
    if cart.buyer_id != user_id:
        return abort(403)
    if quantity_list is None or len(quantity_list) == 0:
        return redirect(url_for("carts.cart"))

    buyer_cart = BuyerCart.query.filter_by(cart_id=cart_id).all()
    # Checking if the quantity_list is integer or can be mapped to list
    quantity_list = eval(quantity_list)
    if buyer_cart is None or len(buyer_cart) == 0:
        return redirect(url_for('carts.cart'))
    if type(quantity_list) is int:
        buyer_cart[0].quantity = quantity_list
    else:
        for i in range(len(quantity_list)):
            buyer_cart[i].quantity = int(quantity_list[i])

    db.session.commit()
    return redirect(url_for("carts.cart"))


@carts.route("/checkout/user<int:user_id>,/cart<int:cart_id>",
          methods=["GET", "POST"])
@login_required
def checkout(user_id, cart_id):
    '''
    Generates the invoice after the successfull transaction. The invoice is saved in the
    static/invoices directory.
    '''
    if current_user.id != user_id:
        return abort(403)
    
    cart = Cart.query.get(cart_id)
    if cart is None:
        return abort(404)
    if cart.buyer_id != user_id:
        return abort(403)
    
    buyer_cart_list = cart.buyer_cart
    if len(buyer_cart_list) == 0:
        flash("Your cart is empty", "info")
        return redirect(url_for("carts.cart"))
    for buyer_cart in buyer_cart_list:
        # Updating the remaining stock
        stock = buyer_cart.product.product_variants[0].stock
        if stock >= buyer_cart.quantity:
            rem_stock = stock - buyer_cart.quantity
            buyer_cart.product.product_variants[0].stock = rem_stock
        else:
            flash(f"Only {buyer_cart.product.product_variants[0].stock} pieces of {buyer_cart.product.name} are left.", "info")
            return redirect(url_for("carts.cart"))

        # Updating the sales of the product
        buyer_cart.product.sales = buyer_cart.product.sales + buyer_cart.quantity
        # Removing items from the cart
        db.session.delete(buyer_cart)

    # commiting the changes after successfull transaction
    db.session.commit()

    # Rendering the invoice.html file and saving it to record past purchases.
    template = render_template("invoice.html", title="Invoice", cart=cart, buyer_cart_list=buyer_cart_list, amount=UtilityFunctions.get_total_amount(buyer_cart_list))
    template_name = UtilityFunctions.generate_hex_name() + ".html"
    invoice = SoldProducts(buyer_id=user_id, invoice=template_name)
    db.session.add(invoice)
    db.session.commit()
    UtilityFunctions.save_template(template, template_name)

    flash("Your order has been placed successfully. You will receive it shortly.", "success")
    return render_template("checkout.html", title="Checkout", cart=cart, buyer_cart_list=buyer_cart_list, amount=UtilityFunctions.get_total_amount(buyer_cart_list))



@carts.route("/past_purchases/<int:user_id>/invoice_id/<int:invoice_id>")
def invoice(user_id, invoice_id):
    '''
    Loads the invoice from the static/invoices directory.
    '''
    if user_id != current_user.id:
        return abort(403)
    invoice = SoldProducts.query.get(invoice_id)
    if invoice:
        invoice_db = invoice.invoice
        return send_from_directory("static/invoices/", invoice_db)
    return abort(404)
