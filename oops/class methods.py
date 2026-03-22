class laptop:
    charger_type="C-type"
    def __init__(self):
        self.brand="";
        self.price=0;

    def setprice(self,price):
        self.price=price
    
    def getprice(self):
        print(self.price)
    
    @classmethod
    def change_chargertype(cls):
        cls.charger_type="B-type"
        print(cls.charger_type)

    @staticmethod
    def classinfo():
        print("THIS IS A LAPTOP CLASS")

asus=laptop()

asus.setprice(60000)
asus.getprice()

laptop.change_chargertype()
laptop.classinfo()