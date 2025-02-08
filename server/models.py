from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy_serializer import SerializerMixin

metadata = MetaData(
    naming_convention={
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    }
)

db = SQLAlchemy(metadata=metadata)

class Restaurant(db.Model, SerializerMixin):
    __tablename__ = "restaurants"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    address = db.Column(db.String)

    # Relationship with Pizza through RestaurantPizza
    pizzas = relationship("Pizza", secondary="restaurant_pizzas", back_populates="restaurants", cascade="all, delete")

    # Serialization rules to limit recursion depth
    serialize_rules = ("-pizzas",)

    def __repr__(self):
        return f"<Restaurant {self.name}>"

    def to_dict(self, include_relationships=False, exclude=()):
        restaurant_dict = {column.name: getattr(self, column.name) for column in self.__table__.columns}
        
        if include_relationships:
            restaurant_dict["restaurant_pizzas"] = [
                rp.to_dict(include_relationships=True) for rp in self.restaurant_pizzas]
        
        return restaurant_dict


class Pizza(db.Model, SerializerMixin):
    __tablename__ = "pizzas"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    ingredients = db.Column(db.String)

    # Relationship with Restaurant through RestaurantPizza
    restaurants = relationship("Restaurant", secondary="restaurant_pizzas", back_populates="pizzas")

    # Serialization rules to limit recursion depth
    serialize_rules = ("-restaurants",)

    def __repr__(self):
        return f"<Pizza {self.name}, {self.ingredients}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "ingredients": self.ingredients
        }


class RestaurantPizza(db.Model, SerializerMixin):
    __tablename__ = "restaurant_pizzas"

    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Integer, nullable=False)

    # Foreign Keys
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id', ondelete="CASCADE"))
    pizza_id = db.Column(db.Integer, db.ForeignKey('pizzas.id', ondelete="CASCADE"))

    # Relationships
    restaurant = relationship("Restaurant", back_populates="pizzas")
    pizza = relationship("Pizza", back_populates="restaurants", single_parent=True) 

    # Serialization rules to limit recursion depth
    serialize_rules = ("-restaurant", "-pizza")

    # Adding validation 
    @validates('price')
    def validate_price(self, key, price):
        if price < 1 or price > 30:
            raise ValueError("Price must be between 1 and 30.")
        return price

    def __repr__(self):
        return f"<RestaurantPizza ${self.price}>"

    def to_dict(self, include_relationships=False):
        rp_dict = {column.name: getattr(self, column.name) for column in self.__table__.columns}
        if include_relationships:
            rp_dict["pizza"] = self.pizza.to_dict()
            rp_dict["restaurant"] = self.restaurant.to_dict()
        return rp_dict
