from EcommerceStore.models import ProductVariants
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.fields import FloatField, IntegerField, SelectField
from wtforms.fields.simple import SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, ValidationError
from flask_wtf.file import FileField, FileAllowed


def check_slash(form, field):
    if "/" in field.data:
        raise ValidationError("\ is not allowed.")
class ProductForm(FlaskForm):
    name = StringField("Product Name", validators=[DataRequired(), Length(max=50), check_slash])
    keywords = StringField("Keywords", validators=[DataRequired()])
    category = SelectField("Category",
                            validators=[DataRequired()])
    variant = SelectField("Variant",
                            validators=[DataRequired()])
    manufacturer = StringField("Manufacturer", validators=[DataRequired(), Length(max=30), check_slash])
    submit = SubmitField("Next")

class ProductVariantForm(FlaskForm):
    variant_value = StringField("variant value", validators=[DataRequired(), Length(max=30), check_slash])
    sku = StringField("SKU", validators=[DataRequired(), Length(max=100), check_slash])
    price = FloatField("Price", validators=[DataRequired()])
    stock = IntegerField("Stock", validators=[DataRequired()])
    submit = SubmitField("Next")

    def validate_sku(self, sku):
        if len(sku.data) > 100:
            raise ValidationError("Sku must be less than 100 characters.")
        # First fetching product variant
        # If it exists then checking if it is unique
        product_variant = ProductVariants.query.filter_by(sku=sku.data).first()
        if product_variant:
             raise ValidationError("Sku must be unique")

    def validate_stock(self, stock):
        if stock.data <= 0:
            raise ValidationError("Stock must be greater than zero.")

    def validate_price(self, price):
        if price.data <= 0:
            raise ValidationError("Price must be greater than zero.")

class ProductDescAndImagesForm(FlaskForm):
    desc = TextAreaField("Description", validators=[DataRequired(), check_slash])
    img = FileField("Add Image", validators=[DataRequired(), FileAllowed(["jpeg", "png", "jpg", "webp"])])
    submit = SubmitField("Upload")


