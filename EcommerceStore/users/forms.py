from EcommerceStore.models import Variant, Category, Store, User
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.fields import BooleanField,  SelectField
from wtforms.fields.simple import PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, Email, ValidationError
from flask_login.utils import current_user

# Validator that checks every field is free from slash (/) because this may cause error in some cases.
def check_slash(form, field):
    if "/" in field.data:
        raise ValidationError("\ is not allowed.")

class SignUpForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(message="Name field can not be empty!"),
                                          Length(min=3, max=30), check_slash])
    username = StringField('Username', validators=[DataRequired(message="Username field can not be empty!"),
                                            Length(min=3, max=30), check_slash])
    email = StringField('Email', validators=[DataRequired(message="Email field can not be empty!"),
                                            Length(min=5, max=30), Email(), check_slash])
    password = PasswordField("Password", validators=[DataRequired(message="Password field can not be empty!"),
                                            Length(min=8, max=60, message="Password length should be atleast 8 characters!"), check_slash])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(message="Confirm password field can not be empty!"),
                                            EqualTo('password'), check_slash])
    address = StringField("Address", validators=[DataRequired(message="Name field can not be empty!"),
                                                Length(max=100), check_slash])
    role = SelectField("Role", choices=["Buyer", "Seller"],
                            validators=[DataRequired()])
    province = SelectField("Province", choices=["Sindh", "Punjab", "Balochistan", "Khyber Pakhtunkhwa"],
                            validators=[DataRequired()])
    city = SelectField("City", choices=["Karachi", "Hyderabad", "Lahore", "Islamabad", "Peshawar"],
                            validators=[DataRequired()])
    submit = SubmitField("Sign Up")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("This username is already taken!")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("This email is already taken!")

class StoreForm(FlaskForm):
    store_name = StringField("Store name", validators=[DataRequired(), check_slash])
    submit = SubmitField("Update")

    def validate_store_name(self, store_name):
        store = Store.query.filter_by(name=store_name.data.lower()).first()
        if store:
            if store.seller_id != current_user.id:
                raise ValidationError("Another store exists with the same name.")


class SignInForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(message="Email field can not be empty!"),
                                            Length(min=5, max=30), Email(), check_slash])
    password = PasswordField("Password", validators=[DataRequired(message="Password field can not be empty!"),
                                            Length(min=8, max=60, message="Password length should be atleast 8"), check_slash])
    remember_me = BooleanField("Remember me", default='checked')
    submit = SubmitField("Login")

class VariantForm(FlaskForm):
    variant_name = StringField("Variant", validators=[DataRequired(), check_slash])
    submit = SubmitField("Add")

    def validate_variant_name(self, variant_name):
        variant = Variant.query.filter_by(variant_name=variant_name.data.lower()).first()
        if variant:
            raise ValidationError("Variant with the same name already exists.")

class CategoryForm(FlaskForm):
    category_name = StringField("Category", validators=[DataRequired()])
    submit = SubmitField("Add")

    def validate_category_name(self, category_name):
        category = Category.query.filter_by(category=category_name.data.lower()).first()
        if category:
            raise ValidationError("Category with the same name already exists.")

class SubCategoryForm(FlaskForm):
    category_name = SelectField("Parent Category", validators=[DataRequired()])
    sub_category_name = StringField("Sub category", validators=[DataRequired(), check_slash])
    submit = SubmitField("Add")

    def validate_category_name(self, category_name):
        category = Category.query.filter_by(category=category_name.data.lower()).first()
        if category is None:
            raise ValidationError("Category with the given name do not exists.")

    def validate_sub_category_name(self, sub_category_name):
        category = Category.query.filter_by(category=sub_category_name.data.lower()).first()
        if category:
            raise ValidationError("Category with the same name already exists.")

class UpdateCategoryForm(FlaskForm):
    category_name = SelectField("Category", validators=[DataRequired()])
    updated_category_name = StringField("New Name", validators=[DataRequired(), check_slash])
    submit = SubmitField("Update")

    def validate_updated_category_name(self, updated_category_name):
        category = Category.query.filter_by(category=updated_category_name.data.lower()).first()
        if category:
            raise ValidationError("Category with the same name already exists.")

class UpdateVariantForm(FlaskForm):
    variant_name = SelectField("Variant", validators=[DataRequired()])
    updated_variant_name = StringField("New Name", validators=[DataRequired(), check_slash])
    submit = SubmitField("Update")

    def validate_updated_variant_name(self, updated_variant_name):
        variant = Variant.query.filter_by(variant_name=updated_variant_name.data.lower()).first()
        if variant:
            raise ValidationError("Variant with the same name already exists.")