from flask_login.utils import login_required, current_user
from EcommerceStore import db
from flask import render_template, url_for, redirect, flash, abort, request, Blueprint
from EcommerceStore.products.forms import ProductDescAndImagesForm, ProductForm, ProductVariantForm
from EcommerceStore.models import Category, Product, ProductVariants, SellerProducts, User, Variant
from pathlib import Path
from EcommerceStore.utils import UtilityFunctions

products = Blueprint("products", __name__)

@products.route("/new_product", methods=['GET', 'POST'])
@login_required
def add_product_details(product_id=None, name=None, category=None, variant=None, manufacturer=None, keywords=None, variant_value=None, sku=None, price=None, stock=None):
    # Checking if the user is seller
    if current_user.role != 'seller':
        flash("You are not authorized to sell products!", "warning")
        return redirect(url_for('main.home'))
    # Checking if the seller owns the product he is trying to update.
    if request.args.get("product_id") is not None:
        if current_user.seller_products is None:
            return abort(403)
        seller_product = SellerProducts.query.filter_by(product_id=int(request.args.get("product_id")), seller_id=current_user.id).first()
        if seller_product is None:
            return abort(403)

    # Retrieving the user from the database and checking if the store is setup.
    # Redirecting the user to setup_store route if the store is not registerd.
    user = User.query.get(current_user.id)
    if user:
        if len(user.seller_store) == 0:
            flash("Please setup the store before uploading the product", "info")
            return redirect(url_for("users.setup_store"))

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
                form_product.name.data = product.name
                form_product.keywords.data = product.keywords
                form_product.category.data = product.category.id
                form_product.variant.data = product.variant.id
                form_product.manufacturer.data = product.manufacturer
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
        return redirect(url_for("products.add_product_variants", product_id=request.args.get("product_id"), product=name, category=category, variant=variant, manufacturer=manufacturer, keywords=keywords, variant_value=variant_value, sku=sku, price=price, stock=stock))
    return render_template("new_product.html", title="Upload Product", form=form_product)


@products.route("/new_product_variants/product<string:product>/category<string:category>/variant<string:variant>/manufacturer<string:manufacturer>/keywords<string:keywords>", methods=['GET', 'POST'])
@login_required
def add_product_variants(product, category, variant, manufacturer, keywords, product_id=None, variant_value=None, sku=None, price=None, stock=None):
    if current_user.role != 'seller':
        flash("You are not authorized to sell products!", "warning")
        return redirect(url_for('main.home'))

    form = ProductVariantForm()
    # Fetching the data from the url parameters if available
    # Using it to support the back button and update operation to populate the alreay filled fields
    if request.method == 'GET':
        if request.args.get("product_id") is not None:
            # If the product variant exists in the database then retrieving it and populating all the fields.
            product_variant = Product.query.get(int(request.args.get("product_id"))).product_variants[0]
            if product_variant:
                form.variant_value.data = product_variant.value
                form.sku.data = product_variant.sku
                form.price.data = product_variant.price
                form.stock.data = product_variant.stock
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
        return redirect(url_for("products.add_product_desc", product=product, category=category, variant=variant, manufacturer=manufacturer, keywords=keywords, variant_value=variant_value, sku=sku, price=price, stock=stock, product_id=request.args.get("product_id")))

    return render_template("new_product_variants.html", title="Upload Product Variants", form=form,
                          product=product, category=category, variant=variant,
                          manufacturer=manufacturer, keywords=keywords, variant_value=variant_value,
                         sku=sku, price=price, stock=stock, product_id=request.args.get("product_id"))


@products.route("/new_product_variants/product<string:product>/category<string:category>/variant<string:variant>/manufacturer<string:manufacturer>/keywords<string:keywords>/variant_value<string:variant_value>/sku<string:sku>/price<float:price>/stock<int:stock>", methods=['GET', 'POST'])
@login_required
def add_product_desc(product, category, variant, manufacturer, keywords, variant_value, sku, price, stock, product_id=None):
    if current_user.role != "seller":
        flash("You are not authorized to sell products!", "warning")
        return redirect(url_for('main.home'))
    form = ProductDescAndImagesForm()

    if request.args.get("product_id") is not None:
        # If the product description exists in the database then retrieving it and populating all the fields.
        product_variant = Product.query.get(int(request.args.get("product_id"))).product_variants[0]
        if product_variant:
            form.desc.data = product_variant.desc

    if form.validate_on_submit():
        desc = form.desc.data
        # Image uploaded by the user is renamed to random 32 bit digits to
        # avoid the naming clash if the somehow any two images have the same name.
        img_data = form.img.data
        img_name = UtilityFunctions.generate_hex_name()
        img_name = UtilityFunctions.save_picture(img_data, img_name)
        return redirect(url_for("products.upload_product", product=product, category=category, variant=variant, manufacturer=manufacturer, keywords=keywords, variant_value=variant_value, sku=sku, price=price, stock=stock, desc=desc, img=img_name, product_id=request.args.get("product_id")))

    return render_template("product_desc.html", title="Add product description", form=form,
                          product=product, category=category, variant=variant,
                          manufacturer=manufacturer, keywords=keywords, variant_value=variant_value,
                          sku=sku, price=price, stock=stock, product_id=request.args.get("product_id"))


@products.route("/new_product_variants/product<string:product>/category<string:category>/variant<string:variant>/manufacturer<string:manufacturer>/keywords<string:keywords>/variant_value<string:variant_value>/sku<string:sku>/price<float:price>/stock<int:stock>/desc<string:desc>/img<string:img>", methods=['GET', 'POST'])
@login_required
def upload_product(product, category, variant, manufacturer, keywords, variant_value, sku, price, stock, desc, img, product_id=None):
    '''
    This method uploads or updates the product. The previous methods just take 
    the input and pass it to this function. This ensures if anything goes bad 
    while taking the input then product is not at all stored in the database.
    '''
    # Fetching category and variant id from the Variant and Category models.
    category_id = Category.query.filter_by(category=category).first().id
    variant_id = Variant.query.filter_by(variant_name=variant).first().id

    # Checking if the product already exists in the database
    if request.args.get("product_id") is not None:
        product_db = Product.query.get(int(request.args.get("product_id")))
        if product_db:
            product_db.name = product
            product_db.keywords = keywords
            product_db.category_id = category_id
            product_db.variant_id = variant_id
            product_db.manufacturer = manufacturer
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
        product_id = product_new.id

    # Checking if the seller product entry exists in the database
    seller_products_db = SellerProducts.query.filter_by(product_id=product_id, seller_id=current_user.id).first()
    if seller_products_db is None:
        # Now inserting seller and product id in the associating if it does not exists
        seller_products = SellerProducts(
            product_id=product_id, seller_id=current_user.id)
        db.session.add(seller_products)
        db.session.commit()

    # Checking if the product variant exists in the the database
    product_variant_db = ProductVariants.query.get(product_id)
    if product_variant_db:
        product_variant_db.value = variant_value
        product_variant_db.sku = sku
        product_variant_db.price = price
        product_variant_db.stock = stock
        product_variant_db.desc = desc
        UtilityFunctions.delete_picture(product_variant_db.thumbnail_img)
        product_variant_db.thumbnail_img = img
        db.session.commit()
    # Creating and inserting product variant if it does not exist.
    else:
        product_variant = ProductVariants(value=variant_value, sku=sku, price=price, stock=stock,
                                        desc=desc, thumbnail_img=img, seller_id=current_user.id, product_id=product_id, variant_id=variant_id)
        db.session.add(product_variant)
        db.session.commit()

    flash("Product upload successfully.", "success")
    return redirect(url_for('main.home'))

@products.route("/delete_product/<int:product_id>", methods=["GET", "POST"])
@login_required
def delete_product(product_id):
    if current_user.role != "seller" or current_user.seller_products is None:
        return abort(403)
    seller_product = SellerProducts.query.filter_by(product_id=product_id, seller_id=current_user.id).first()
    if seller_product is None:
        return abort(403)
    # Fetching the product, product_variant and seller entry from the respective tables and 
    # then deleting if all exists.
    product = Product.query.get(product_id)
    product_variant = ProductVariants.query.filter_by(product_id=product_id, seller_id=current_user.id).first()
    seller_entry = SellerProducts.query.filter_by(product_id=product_id, seller_id=current_user.id).first()

    if product and product_variant and seller_entry:
        try:
            db.session.delete(product_variant)
            db.session.delete(seller_entry)
            db.session.delete(product)
            db.session.commit()
            UtilityFunctions.delete_picture(product_variant.thumbnail_img)
            flash("Product deleted successfully", "success")
        except:
            flash("Something went wrong", "warning")
    else:
        flash("Product does not exists.")
    return redirect(url_for("main.home"))


@products.route("/product/<int:product_id>")
def product(product_id):
    '''
    Renders the product page.
    '''
    product = Product.query.filter_by(id=product_id).first_or_404()
    img_path = Path('/static/product_images/'+ product.product_variants[0].thumbnail_img)
    return render_template("product.html", title="Product", product=product, img=img_path)

