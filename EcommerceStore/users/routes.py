from flask_login.utils import login_required, login_user, current_user, logout_user
from EcommerceStore import db, bcrypt
from flask import g, render_template, url_for, redirect, flash, abort, request, Blueprint
from EcommerceStore.users.forms import (CategoryForm, SignUpForm, SignInForm, StoreForm, SubCategoryForm,
                                 VariantForm, UpdateCategoryForm, UpdateVariantForm)
from EcommerceStore.models import (SoldProducts, Category, Store, User, Variant)
from EcommerceStore.utils import UtilityFunctions

users = Blueprint("users", __name__)

@users.route("/signUp", methods=['GET', 'POST'])
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
        return redirect(url_for('users.sign_in'))
    return render_template("signUp.html", title='Register', form=form)


@users.route("/setup_store", methods=["POST", "GET"])
@login_required
def setup_store():
    if current_user.role != "seller":
        flash("Only authorized seller accounts can setup their store.", "warning")
        return redirect(url_for("main.home"))
    form = StoreForm()
    # If the request method is GET and user has already setup their store name then 
    # retreiving the store name from the database if it exists and populating it in the store name field.
    if request.method == 'GET':
        store = Store.query.filter_by(seller_id=current_user.id).first()
        if store:
            form.store_name.data = str(store.name).title()

    if form.validate_on_submit():
        store_name = Store(name=form.store_name.data.lower(), seller_id=current_user.id)
        # If store name already exists in the database then update operation is performed.
        store = Store.query.filter_by(seller_id=current_user.id).first()
        if store:
            store.name = form.store_name.data.lower()
            s = "updated"
        else:
            db.session.add(store_name)
            s = "created"

        db.session.commit()
        msg = f"Store has been {s} successfully."
        flash(msg, "info")
        return redirect(url_for("main.home"))
    return render_template("store.html", form=form, title="Store.html")


@users.route("/signIn", methods=['GET', 'POST'])
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
            return redirect(next or url_for('main.home'))
        else:
            flash("Please check your email or password.", "danger")
        return redirect(url_for('users.sign_in'))
    return render_template("signin.html", title='Login', form=form)


@users.route("/signOut", methods=['GET', 'POST'])
def sign_out():
    logout_user()
    flash("Logged out successfully!", "success")
    return redirect(url_for("main.home"))

@users.route("/admin/add_variants", methods=["GET", "POST"])
def add_variant():
    '''
    Lets the user to add variants. This method is restricted to only admins.
    '''
    if current_user.is_authenticated and current_user.role == "admin":
        form = VariantForm()
        if form.validate_on_submit():
            variant_name = Variant(variant_name=form.variant_name.data.lower())
            db.session.add(variant_name)
            db.session.commit()
            flash("Variant added successfully.", "success")
            return redirect(url_for("users.add_variant"))
        return render_template("variant.html", form=form, title="Add New Variants")
    else:
        return abort(403)

@users.route("/admin/add_category", methods=["GET", "POST"])
def add_category():
    '''
    Lets the user to add parent categories. This method is restricted to only admins.
    '''
    if current_user.is_authenticated and current_user.role == "admin":
        form = CategoryForm()
        if form.validate_on_submit():
            category_name = Category(category=form.category_name.data.lower())
            db.session.add(category_name)
            db.session.commit()
            UtilityFunctions.set_parent_category(form.category_name.data.lower())
            flash("Category added successfully.", "success")
            return redirect(url_for("users.add_category"))
        return render_template("category.html", form=form, title="Add New Category")
    else:
        return abort(403)

@users.route("/admin/add_subcategory", methods=["GET", "POST"])
def add_subcategory():
    '''
    Lets the user to add subcategories. This method is restricted to only admins.
    '''
    if current_user.is_authenticated and current_user.role == "admin":
        form = SubCategoryForm()
        # Populating the drop down menu with the parent categories.
        form.category_name.choices = list(map(str.title, list(map(str, UtilityFunctions.get_parent_categories()))))
        if form.validate_on_submit():
            parent_category = Category.query.filter_by(category=form.category_name.data.lower()).first()
            sub_category = form.sub_category_name.data.lower()
            # Setting the parent_id attribute to the parent category id.
            category = Category(category=sub_category, parent_id=parent_category.id)
            db.session.add(category)
            db.session.commit()
            flash("Subcategory added successfully.", "success")
            return redirect(url_for("users.add_subcategory"))
        return render_template("sub_category.html", form=form, title="Add New Sub Category")
    else:
        return abort(403)

@users.route("/admin/update_category", methods=["GET", "POST"])
def update_category():
    '''
    Lets the user to update the categories. This method is restricted to only admins.
    '''
    if current_user.is_authenticated and current_user.role == "admin":
        form = UpdateCategoryForm()
        form.category_name.choices = list(map(str.title, list(map(str, UtilityFunctions.get_categories()))))
        if form.validate_on_submit():
            old_category = Category.query.filter_by(category=form.category_name.data.lower()).first()
            updated_category = form.updated_category_name.data.lower()
            old_category.category = updated_category
            db.session.commit()
            flash("Category updated successfully", "success")
            return redirect(url_for("main.home"))
        return render_template("update_category.html", form=form, title="Update Category")
    else:
        return abort(403)

@users.route("/admin/update_variant", methods=["GET", "POST"])
def update_variant():
    '''
    Lets the user to update the variants. This method is restricted to only admins.
    '''
    if current_user.is_authenticated and current_user.role == "admin":
        form = UpdateVariantForm()
        form.variant_name.choices = list(map(str.title, list(map(str, UtilityFunctions.get_variants()))))
        if form.validate_on_submit():
            old_variant = Variant.query.filter_by(variant_name=form.variant_name.data.lower()).first()
            updated_variant = form.updated_variant_name.data.lower()
            old_variant.variant_name = updated_variant
            db.session.commit()
            flash("Variant updated successfully", "success")
            return redirect(url_for("main.home"))
        return render_template("update_variant.html", form=form, title="Update Variant")
    else:
        return abort(403)

@users.route("/past_puchases/<int:user_id>")
def past_purchases(user_id):
    '''
    Keeps track of the shopping history of the customer.
    '''
    if user_id != current_user.id:
        return abort(403)

    invoice = SoldProducts.query.filter_by(buyer_id=user_id).order_by(SoldProducts.id.desc()).all()
    templates = []
    for past_record in  invoice:
        templates.append(past_record)
    return render_template("past_purchases.html", templates=templates)