from flask_login.utils import login_required, login_user, current_user, logout_user
from EcommerceStore import app, db, bcrypt
from flask import render_template, url_for, redirect, flash, abort, request, g, send_from_directory
from EcommerceStore.forms import (CategoryForm, ProductDescAndImagesForm, ProductForm,
                                 ProductVariantForm,SignUpForm, SignInForm, StoreForm, SubCategoryForm,
                                 VariantForm, UpdateCategoryForm, UpdateVariantForm)
from EcommerceStore.models import (SoldProducts, Cart, BuyerCart, Category, Product, ProductVariants, SellerProducts,
                                  Store, User, Variant)
from pathlib import Path
from EcommerceStore.utils import UtilityFunctions
from datetime import timedelta, datetime

@app.before_request
def load_categories():
    '''
    This method is called before any request is made.
    It ensures that several builtin types are available in html layouts. 
    '''
    categories = Category.query.all()
    parent_categories = []
    for parent in categories:
        if parent.get_id() == parent.get_parent_id():
            parent_categories.append(parent)

    # g in flask is a global variable that is accessible from anywhere.
    # Assigning bultin types to g variable lets us use these types in html templates.
    g.categories = parent_categories
    g.length = len(parent_categories)
    g.str = str
    g.len = len
    g.list = list
    g.round = round
    g.float = float
    g.timedelta = timedelta
    g.datetime = datetime

@app.route("/")
@app.route("/home")
def home():
    title = "A place where only approved brands can sell."
    all_products = []
    users = User.query.all()
    for seller in users:
        if seller.get_role() == "seller":
            for seller_product in seller.seller_products:
                img_path = Path('static/product_images')
                img_path = img_path.joinpath(seller_product.product.product_variants[0].get_thumbnail_img())
                seller_product = (seller, seller_product.product.get_name(), seller_product.product.product_variants[0].get_price(),
                img_path, seller.seller_store[0].get_name(), seller_product.product.get_id())
                all_products.append(seller_product)
    return render_template("home.html", title=title, users=users, products=all_products, round=round)


@app.route("/signUp", methods=['GET', 'POST'])
def sign_up():
    form = SignUpForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        name = form.name.data.lower()
        username = form.username.data.lower()
        email = form.email.data.lower()
        password = hashed_pw
        address = form.address.data.lower()
        province = form.province.data.lower()
        city = form.city.data.lower()
        role = form.role.data.lower()
        if email == 'admin@admin.com':
            role = 'admin'
        user = User(name=name, username=username, email=email, password=password, address=address,
                    province=province, city=city, role=role)
        db.session.add(user)
        db.session.commit()
        flash("Your account has been created successfully! You can now login.", 'success')
        return redirect(url_for('sign_in'))
    return render_template("signUp.html", title='Register', form=form)


@app.route("/setup_store", methods=["POST", "GET"])
@login_required
def setup_store():
    if current_user.get_role() != "seller":
        flash("Only authorized seller accounts can setup their store.", "warning")
        return redirect(url_for("home"))
    form = StoreForm()
    # If the request method is GET and user has already setup their store name then 
    # retreiving the store name from the database if it exists and populating it in the store name field.
    if request.method == 'GET':
        store = Store.query.filter_by(seller_id=current_user.get_id()).first()
        if store:
            form.store_name.data = str(store.get_name()).title()

    if form.validate_on_submit():
        store_name = Store(name=form.store_name.data.lower(), seller_id=current_user.get_id())
        # If store name already exists in the database then update operation is performed.
        store = Store.query.filter_by(seller_id=current_user.get_id()).first()
        if store:
            store.name = form.store_name.data.lower()
            s = "updated"
        else:
            db.session.add(store_name)
            s = "created"

        db.session.commit()
        msg = f"Store has been {s} successfully."
        flash(msg, "info")
        return redirect(url_for("home"))
    return render_template("store.html", form=form, title="Store.html")


@app.route("/signIn", methods=['GET', 'POST'])
def sign_in():
    form = SignInForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash("Login Successfull!", "success")
            # If the user tries to access some route that requires login then
            # this line of code stores the url of that route and redirects the user
            # to that url after he has logged in successfully.
            next = request.args.get('next')
            return redirect(next or url_for('home'))
        else:
            flash("Please check your email or password.", "danger")
        return redirect(url_for('home'))
    return render_template("signin.html", title='Login', form=form)


@app.route("/signOut", methods=['GET', 'POST'])
def sign_out():
    logout_user()
    flash("Logged out successfully!", "success")
    return redirect(url_for("home"))

@app.route("/new_product", methods=['GET', 'POST'])
@login_required
def add_product_details(product_id=None, name=None, category=None, variant=None, manufacturer=None, keywords=None, variant_value=None, sku=None, price=None, stock=None):
    # Checking if the user is seller
    if current_user.get_role() != 'seller':
        flash("You are not authorized to sell products!", "warning")
        return redirect(url_for('home'))

    # Checking if the seller owns the product he is trying to update.
    if request.args.get("product_id") is not None:
        if current_user.seller_products is None:
            return abort(403)

    # Retrieving the user from the database and checking if the store is setup.
    # Redirecting the user to setup_store route if the store is not registerd.
    user = User.query.get(current_user.get_id())
    if user:
        if len(user.seller_store) == 0:
            flash("Please setup the store before uploading the product", "info")
            return redirect(url_for("setup_store"))

    form_product = ProductForm()
    # Fetching all the categories and variants available from the database and populating the dropdown menu
    # with the retrieved values.
    form_product.category.choices = list(map(str.title, list(map(str, UtilityFunctions.get_categories())))) 
    form_product.variant.choices = list(map(str.title, list(map(str, UtilityFunctions.get_variants()))))

    # Fetching the data from the url parameters if available
    # Using it to support the back button and update operation to populate the alreay filled fields
    if request.method == 'GET':
        if request.args.get('product_id') is not None:
            # If the product exists in the database then retrieving it and populating all the fields.
            product = Product.query.get(int(request.args.get('product_id')))
            if product:
                form_product.name.data = product.get_name()
                form_product.keywords.data = product.get_keywords()
                form_product.category.data = product.category
                form_product.variant.data = product.variant
                form_product.manufacturer.data = product.get_manufacturer()
        else:
            if request.args.get('product') is not None:
                form_product.name.data = request.args.get('product')
            if request.args.get('category') is not None:
                form_product.category.data = request.args.get('category')
            if request.args.get('variant') is not None:
                form_product.variant.data = request.args.get('variant')
            if request.args.get('manufacturer') is not None:
                form_product.manufacturer.data = request.args.get('manufacturer')
            if request.args.get('keywords') is not None:
                form_product.keywords.data = request.args.get('keywords')

    if form_product.validate_on_submit():
        # Fetching all the data of the form belonging to the products table
        name = form_product.name.data.lower()
        category = form_product.category.data.lower()
        variant = form_product.variant.data.lower()
        manufacturer = form_product.manufacturer.data.lower()
        keywords = form_product.keywords.data.lower()
        return redirect(url_for("add_product_variants", product_id=request.args.get("product_id"), product=name, category=category, variant=variant, manufacturer=manufacturer, keywords=keywords, variant_value=variant_value, sku=sku, price=price, stock=stock))
    return render_template("new_product.html", title="Upload Product", form=form_product)


@app.route("/new_product_variants/product<string:product>/category<string:category>/variant<string:variant>/manufacturer<string:manufacturer>/keywords<string:keywords>", methods=['GET', 'POST'])
@login_required
def add_product_variants(product, category, variant, manufacturer, keywords, product_id=None, variant_value=None, sku=None, price=None, stock=None):
    if current_user.get_role() != 'seller':
        flash("You are not authorized to sell products!", "warning")
        return redirect(url_for('home'))

    form = ProductVariantForm()
    # Fetching the data from the url parameters if available
    # Using it to support the back button and update operation to populate the alreay filled fields
    if request.method == 'GET':
        if request.args.get("product_id") is not None:
            # If the product variant exists in the database then retrieving it and populating all the fields.
            product_variant = Product.query.get(int(request.args.get("product_id"))).product_variants[0]
            if product_variant:
                form.variant_value.data = product_variant.get_value()
                form.sku.data = product_variant.get_sku()
                form.price.data = product_variant.get_price()
                form.stock.data = product_variant.get_stock()
        else:
            if request.args.get("variant_value") is not None:
                form.variant_value.data = request.args.get("variant_value")
            if request.args.get("sku") is not None:
                form.sku.data = request.args.get("sku")
            if request.args.get("price") is not None:
                form.price.data = request.args.get("price")
            if request.args.get("stock") is not None:
                form.stock.data = request.args.get("stock")

    if form.validate_on_submit():
        # Now fetching all the remaining data that belongs to ProductVariants table
        variant_value = form.variant_value.data.lower()
        sku = form.sku.data
        price = form.price.data
        stock = form.stock.data
        return redirect(url_for("add_product_desc", product=product, category=category, variant=variant, manufacturer=manufacturer, keywords=keywords, variant_value=variant_value, sku=sku, price=price, stock=stock, product_id=request.args.get("product_id")))

    return render_template("new_product_variants.html", title="Upload Product Variants", form=form,
                          product=product, category=category, variant=variant,
                          manufacturer=manufacturer, keywords=keywords, variant_value=variant_value,
                         sku=sku, price=price, stock=stock, product_id=request.args.get("product_id"))


@app.route("/new_product_variants/product<string:product>/category<string:category>/variant<string:variant>/manufacturer<string:manufacturer>/keywords<string:keywords>/variant_value<string:variant_value>/sku<string:sku>/price<float:price>/stock<int:stock>", methods=['GET', 'POST'])
@login_required
def add_product_desc(product, category, variant, manufacturer, keywords, variant_value, sku, price, stock, product_id=None):
    if current_user.get_role() != "seller":
        flash("You are not authorized to sell products!", "warning")
        return redirect(url_for('home'))
    form = ProductDescAndImagesForm()

    if request.args.get("product_id") is not None:
        # If the product description exists in the database then retrieving it and populating all the fields.
        product_variant = Product.query.get(int(request.args.get("product_id"))).product_variants[0]
        if product_variant:
            form.desc.data = product_variant.get_desc()

    if form.validate_on_submit():
        desc = form.desc.data
        # Image uploaded by the user is renamed to random 32 bit digits to
        # avoid the naming clash if the somehow any two images have the same name.
        img_data = form.img.data
        img_name = UtilityFunctions.generate_hex_name()
        img_name = UtilityFunctions.save_picture(img_data, img_name)
        return redirect(url_for("upload_product", product=product, category=category, variant=variant, manufacturer=manufacturer, keywords=keywords, variant_value=variant_value, sku=sku, price=price, stock=stock, desc=desc, img=img_name, product_id=request.args.get("product_id")))

    return render_template("product_desc.html", title="Add product description", form=form,
                          product=product, category=category, variant=variant,
                          manufacturer=manufacturer, keywords=keywords, variant_value=variant_value,
                          sku=sku, price=price, stock=stock, product_id=request.args.get("product_id"))


@app.route("/new_product_variants/product<string:product>/category<string:category>/variant<string:variant>/manufacturer<string:manufacturer>/keywords<string:keywords>/variant_value<string:variant_value>/sku<string:sku>/price<float:price>/stock<int:stock>/desc<string:desc>/img<string:img>", methods=['GET', 'POST'])
@login_required
def upload_product(product, category, variant, manufacturer, keywords, variant_value, sku, price, stock, desc, img, product_id=None):
    '''
    This method uploads or updates the product. The previous methods just take 
    the input and pass it to this function. This ensures if anything goes bad 
    while taking the input then product is not at all stored in the database.
    '''
    # Fetching category and variant id from the Variant and Category models.
    category_id = Category.query.filter_by(category=category).first().get_id()
    variant_id = Variant.query.filter_by(variant_name=variant).first().get_id()

    # Checking if the product already exists in the database
    if request.args.get("product_id") is not None:
        product_db = Product.query.get(int(request.args.get("product_id")))
        if product_db:
            product_db.set_name(product)
            product_db.set_keywords(keywords)
            product_db.set_category_id(category_id)
            product_db.set_variant_id(variant_id)
            product_db.set_manufacturer(manufacturer)
            db.session.commit()

    # Creating and inserting the new product if it does not exist
    else:
        product_new = Product(name=product, category_id=category_id,
                          variant_id=variant_id, manufacturer=manufacturer, keywords=keywords)
        db.session.add(product_new)
        db.session.commit()

    # This checks if the product id is in query parameter and if it exists then type casting
    # it to the integer type. If it does not exist then simply retreiving it from the newly created product. 
    if request.args.get("product_id") is not None:
        product_id = int(request.args.get("product_id"))
    else:
        product_id = product_new.get_id()

    # Checking if the seller product entry exists in the database
    seller_products_db = SellerProducts.query.filter_by(product_id=product_id, seller_id=current_user.get_id()).first()
    if seller_products_db is None:
        # Now inserting seller and product id in the associating if it does not exists
        seller_products = SellerProducts(
            product_id=product_id, seller_id=current_user.get_id())
        db.session.add(seller_products)
        db.session.commit()

    # Checking if the product variant exists in the the database
    product_variant_db = ProductVariants.query.get(product_id)
    if product_variant_db:
        product_variant_db.set_value(variant_value)
        product_variant_db.set_sku(sku)
        product_variant_db.set_price(price)
        product_variant_db.set_stock(stock)
        product_variant_db.set_desc(desc)
        product_variant_db.set_thumbnail_img(img)
        db.session.commit()
    # Creating and inserting product variant if it does not exist.
    else:
        product_variant = ProductVariants(value=variant_value, sku=sku, price=price, stock=stock,
                                        desc=desc, thumbnail_img=img, seller_id=current_user.get_id(), product_id=product_id, variant_id=variant_id)
        db.session.add(product_variant)
        db.session.commit()

    flash("Product upload successfully.", "success")
    return redirect(url_for('home'))

@app.route("/delete_product/<int:product_id>", methods=["GET", "POST"])
@login_required
def delete_product(product_id):
    if current_user.get_role() != "seller" or current_user.seller_products is None:
        return abort(403)

    # Fetching the product, product_variant and seller entry from the respective tables and 
    # then deleting if all exists.
    product = Product.query.get(product_id)
    product_variant = ProductVariants.query.filter_by(product_id=product_id, seller_id=current_user.get_id()).first()
    seller_entry = SellerProducts.query.filter_by(product_id=product_id, seller_id=current_user.get_id()).first()

    if product and product_variant and seller_entry:
        try:
            db.session.delete(product_variant)
            db.session.delete(seller_entry)
            db.session.delete(product)
            db.session.commit()
            flash("Product deleted successfully", "success")
        except:
            flash("Something went wrong", "warning")
    else:
        flash("Product does not exists.")
    return redirect(url_for("home"))

@app.route("/admin/add_variants", methods=["GET", "POST"])
def add_variant():
    '''
    Lets the user to add variants. This method is restricted to only admins.
    '''
    if current_user.is_authenticated and current_user.get_role() == "admin":
        form = VariantForm()
        if form.validate_on_submit():
            variant_name = Variant(variant_name=form.variant_name.data.lower())
            db.session.add(variant_name)
            db.session.commit()
            flash("Variant added successfully.", "success")
            return redirect(url_for("add_variant"))
        return render_template("variant.html", form=form, title="Add New Variants")
    else:
        return abort(403)

@app.route("/admin/add_category", methods=["GET", "POST"])
def add_category():
    '''
    Lets the user to add parent categories. This method is restricted to only admins.
    '''
    if current_user.is_authenticated and current_user.get_role() == "admin":
        form = CategoryForm()
        if form.validate_on_submit():
            category_name = Category(category=form.category_name.data.lower())
            db.session.add(category_name)
            db.session.commit()
            UtilityFunctions.set_parent_category(form.category_name.data.lower())
            flash("Category added successfully.", "success")
            return redirect(url_for("add_category"))
        return render_template("category.html", form=form, title="Add New Category")
    else:
        return abort(403)

@app.route("/admin/add_subcategory", methods=["GET", "POST"])
def add_subcategory():
    '''
    Lets the user to add subcategories. This method is restricted to only admins.
    '''
    if current_user.is_authenticated and current_user.get_role() == "admin":
        form = SubCategoryForm()
        # Populating the drop down menu with the parent categories.
        form.category_name.choices = list(map(str.title, list(map(str, UtilityFunctions.get_parent_categories()))))
        if form.validate_on_submit():
            parent_category = Category.query.filter_by(category=form.category_name.data.lower()).first()
            sub_category = form.sub_category_name.data.lower()
            # Setting the parent_id attribute to the parent category id.
            category = Category(category=sub_category, parent_id=parent_category.get_id())
            db.session.add(category)
            db.session.commit()
            flash("Subcategory added successfully.", "success")
            return redirect(url_for("add_subcategory"))
        return render_template("sub_category.html", form=form, title="Add New Sub Category")
    else:
        return abort(403)

@app.route("/admin/update_category", methods=["GET", "POST"])
def update_category():
    '''
    Lets the user to update the categories. This method is restricted to only admins.
    '''
    if current_user.is_authenticated and current_user.get_role() == "admin":
        form = UpdateCategoryForm()
        form.category_name.choices = list(map(str.title, list(map(str, UtilityFunctions.get_categories()))))
        if form.validate_on_submit():
            old_category = Category.query.filter_by(category=form.category_name.data.lower()).first()
            updated_category = form.updated_category_name.data.lower()
            old_category.set_category(updated_category)
            db.session.commit()
            flash("Category updated successfully", "success")
            return redirect(url_for("home"))
        return render_template("update_category.html", form=form, title="Update Category")
    else:
        return abort(403)

@app.route("/admin/update_variant", methods=["GET", "POST"])
def update_variant():
    '''
    Lets the user to update the variants. This method is restricted to only admins.
    '''
    if current_user.is_authenticated and current_user.get_role() == "admin":
        form = UpdateVariantForm()
        form.variant_name.choices = list(map(str.title, list(map(str, UtilityFunctions.get_variants()))))
        if form.validate_on_submit():
            old_variant = Variant.query.filter_by(variant_name=form.variant_name.data.lower()).first()
            updated_variant = form.updated_variant_name.data.lower()
            old_variant.setvariant_name(updated_variant)
            db.session.commit()
            flash("Variant updated successfully", "success")
            return redirect(url_for("home"))
        return render_template("update_variant.html", form=form, title="Update Variant")
    else:
        return abort(403)

@app.route("/product/<int:product_id>")
def product(product_id):
    '''
    Renders the product page.
    '''
    product = Product.query.filter_by(id=product_id).first_or_404()
    img_path = Path('/static/product_images/'+ product.product_variants[0].get_thumbnail_img())
    return render_template("product.html", title="Product", product=product, img=img_path)

@app.route("/product/<int:product_id>/cart", methods=["GET", "POST"])
@login_required
def add_to_cart(product_id):
    product = Product.query.filter_by(id=product_id).first_or_404()
    buyer = User.query.get(current_user.get_id())
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
        bc = BuyerCart(cart_id=cart.get_id(), product_id=product.get_id(), quantity=1)
        db.session.add(bc)
        db.session.commit()
    else:
        bc = BuyerCart.query.filter_by(cart_id=cart.get_id(), product_id=product.get_id()).first()
        if bc is None:
            # check if the product already exists
            bc = BuyerCart(cart_id=cart.get_id(), product_id=product.get_id(), quantity=1)
            db.session.add(bc)
            db.session.commit()
        else:
            # Just incrementing the quantity if the prouct is already there in the cart
            bc.quantity += 1

    db.session.commit()
    return redirect(url_for('cart_show', cart_id=cart.id, user_id=current_user.get_id()))


@app.route("/cart", methods=["GET", "POST"])
@login_required
def cart():
    '''
    Creates the cart object in the database if it does not exist.
    '''
    user_id = current_user.get_id()
    cart = Cart.query.filter_by(buyer_id=user_id).first()
    if cart is None:
        cart = Cart(buyer_id=user_id)
        db.session.add(cart)
        db.session.commit()
    return redirect(url_for("cart_show", cart_id=cart.get_id(), user_id=user_id))

@app.route("/cart/<int:cart_id>/<int:user_id>", methods=["GET","POST"])
@login_required
def cart_show(cart_id, user_id):
    # Checking if the user is trying to access only his cart
    if current_user.get_id() != user_id:
        return abort(403)

    cart = Cart.query.get(cart_id)
    # Checks if the cart exists.
    if cart is None:
        return abort(404)

    # If the cart does not belong to the user trying to access then returns 403 error.
    if cart.buyer.get_id() != user_id:
        return abort(403)
    
    if request.method == 'GET':
        if request.args.get('quantity'):
            # Fetches quantity_list url parameter
            quantity_list = request.args.getlist("quantity")
            return redirect(url_for("generate_bill", cart_id=cart_id, user_id=user_id, quantity_list=quantity_list))
    return render_template("cart.html", title="Cart", cart=cart)

@app.route("/cart/<int:cart_id>/<int:user_id>/<int:product_id>", methods=["GET","POST"])
@login_required
def remove_product_cart(cart_id, user_id, product_id):
    if current_user.get_id() != user_id:
        return abort(403)

    cart = Cart.query.get(cart_id)
    if cart is None:
        return abort(404)

    if cart.buyer.get_id() != user_id:
        return abort(403)

    buyer_cart = BuyerCart.query.filter_by(cart_id=cart_id, product_id=product_id).first()
    if buyer_cart is not None:
        db.session.delete(buyer_cart)
        db.session.commit()

    return redirect(url_for("cart_show",cart_id=cart_id, user_id=user_id))

@app.route("/generate_bill/cart/<int:cart_id>/<int:user_id>/quantity<string:quantity_list>", methods=["GET", "POST"])
@login_required
def generate_bill(cart_id, user_id, quantity_list=None):
    '''
    Generates the bill of the individual product.
    '''
    if current_user.get_id() != user_id:
        return abort(403)

    cart = Cart.query.get(cart_id)
    if cart is None:
        return abort(404)
    if cart.buyer_id != user_id:
        return abort(403)
    if quantity_list is None or len(quantity_list) == 0:
        return redirect(url_for("cart"))

    buyer_cart = BuyerCart.query.filter_by(cart_id=cart_id).all()
    # Checking if the quantity_list is integer or can be mapped to list
    quantity_list = eval(quantity_list)
    if buyer_cart is None or len(buyer_cart) == 0:
        return redirect(url_for('cart'))
    if type(quantity_list) is int:
        buyer_cart[0].set_quantity(quantity_list)
    else:
        for i in range(len(quantity_list)):
            buyer_cart[i].set_quantity(int(quantity_list[i]))

    db.session.commit()
    return redirect(url_for("cart"))


@app.route("/checkout/user<int:user_id>,/cart<int:cart_id>",
          methods=["GET", "POST"])
@login_required
def checkout(user_id, cart_id):
    '''
    Generates the invoice after the successfull transaction. The invoice is saved in the
    static/invoices directory.
    '''
    if current_user.get_id() != user_id:
        return abort(403)
    
    cart = Cart.query.get(cart_id)
    if cart is None:
        return abort(404)
    if cart.get_buyer_id() != user_id:
        return abort(403)
    
    buyer_cart_list = cart.buyer_cart
    if len(buyer_cart_list) == 0:
        flash("Your cart is empty", "info")
        return redirect(url_for("cart"))
    for buyer_cart in buyer_cart_list:
        # Updating the remaining stock
        stock = buyer_cart.product.product_variants[0].get_stock()
        if stock >= buyer_cart.get_quantity():
            rem_stock = stock - buyer_cart.get_quantity()
            buyer_cart.product.product_variants[0].set_stock(rem_stock)
        else:
            flash(f"Only {buyer_cart.product.product_variants[0].get_stock()} peices of {buyer_cart.product.get_name()} are left.", "info")
            return redirect(url_for("cart"))

        # Updating the sales of the product
        buyer_cart.product.set_sales(buyer_cart.product.get_sales() + buyer_cart.get_quantity())
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

@app.route("/past_puchases/<int:user_id>")
def past_purchases(user_id):
    '''
    Keeps track of the shopping history of the customer.
    '''
    if user_id != current_user.get_id():
        return abort(403)

    invoice = SoldProducts.query.filter_by(buyer_id=user_id).order_by(SoldProducts.id.desc()).all()
    templates = []
    for past_record in  invoice:
        templates.append(past_record)
    return render_template("past_purchases.html", templates=templates)

@app.route("/past_purchases/<int:user_id>/invoice_id/<int:invoice_id>")
def invoice(user_id, invoice_id):
    '''
    Loads the invoice from the static/invoices directory.
    '''
    if user_id != current_user.get_id():
        return abort(403)
    invoice = SoldProducts.query.get(invoice_id)
    if invoice:
        invoice_db = invoice.get_invoice()
        return send_from_directory("static/invoices/", invoice_db)
    return abort(404)
