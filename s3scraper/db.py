from sqlalchemy import Column, Float, ForeignKey, Integer, String, create_engine, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

DB_PATH = "s3scraper.db"

Base = declarative_base()


class Search(Base):
    __tablename__ = "search"

    id = Column(Integer, primary_key=True)
    search_params = Column(Text)
    site = Column(String)

    # SQLite doesn't support datetime :(
    search_date = Column(String, server_default=str(datetime.now()))


class Product(Base):
    __tablename__ = "product"

    id = Column(Integer, primary_key=True)
    name = Column(Text)


class AmazonProduct(Product):
    __mapper_args__ = {'polymorphic_identity': 'amazon_product'}

    ASIN = Column(String)

class AliexpressProduct(Product):
    __mapper_args__ = {'polymorphic_identity': 'aliexpress_product'}

    ID = Column(String)

class EbayProduct(Product):
    __mapper_args__ = {'polymorphic_identity': 'ebay_product'}

    ebay_id = Column(String)


class TPProduct(Product):
    __mapper_args__ = {'polymorphic_identity': 'tp_product'}

    tp_id = Column(String)


class ProductDetail(Base):
    __tablename__ = "product_detail"

    id = Column(Integer, primary_key=True)
    product = Column(Integer, ForeignKey("product.id"))

    overview = Column(Text)
    description = Column(Text)
    location = Column(Text)
    rating = Column(Float)
    review_numbers = Column(Integer)

    price = Column(String)
    currency = Column(String)

    price_per_unit = Column(String)
    units = Column(String)

    url = Column(String)
    image_url = Column(String)
    seller = Column(String)
    seller_url = Column(Text)
    seller_rating = Column(String)

    html_file = Column(String)

    search = Column(Integer, ForeignKey("search.id"))


def initialize_db():
    engine = create_engine("sqlite:///{}".format(DB_PATH), echo=False)
    Base.metadata.create_all(engine)
    return engine


def create_session(engine=None):
    if not engine:
        engine = initialize_db()
    return sessionmaker(bind=engine)()
