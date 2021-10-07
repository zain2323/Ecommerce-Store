from flask import Blueprint, g, render_template
from EcommerceStore.models import User
from pathlib import Path

main = Blueprint("main", __name__)

@main.route("/")
@main.route("/home")
def home():
    title = "A place where only approved brands can sell."
    all_products = []
    users = User.query.all()
    for seller in users:
        if seller.role == "seller":
            for seller_product in seller.seller_products:
                img_path = Path('static/product_images')
                img_path = img_path.joinpath(seller_product.product.product_variants[0].thumbnail_img)
                seller_product = (seller, seller_product.product.name, seller_product.product.product_variants[0].price,
                img_path, seller.seller_store[0].name, seller_product.product.id)
                all_products.append(seller_product)
    return render_template("home.html", title=title, users=users, products=all_products, round=round)
