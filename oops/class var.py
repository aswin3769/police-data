class phone:
    charger_type="C-type"
    def __init__(self,brand,os):
        self.brand=brand;
        self.os=os;
    def display(self):
        print("BRAND :",self.brand)
        print("OS :",self.os)
        print("CHARGER TYPE :",self.charger_type)


samsung=phone("samsung","android os")
samsung.display()

iphone=phone("iphone","ios")
iphone.display()
