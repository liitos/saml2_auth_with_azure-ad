from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id_, given_name, family_name, email, ):
        self.id = id_
        self.given_name = given_name
        self.family_name = family_name
        self.email = email
        
        