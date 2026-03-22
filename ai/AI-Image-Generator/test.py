import requests
import cv2
from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk
import numpy as np

# URL of the Flask server
FLASK_URL = "http://localhost:5000/swap-face"

# Initialize tkinter window
window = Tk()
window.title("Face Swap App")
window.geometry("800x600")

# Display area for the image
image_label = Label(window)
image_label.pack()

# Function to open and process the image
def open_image():
    file_path = filedialog.askopenfilename()
    if not file_path:
        return

    frame = cv2.imread(file_path)
    _, img_encoded = cv2.imencode('.jpg', frame)
    files = {'frame': img_encoded.tobytes()}

    try:
        response = requests.post(FLASK_URL, files=files)
        if response.status_code == 200:
            img_data = np.frombuffer(response.content, np.uint8)
            img = cv2.imdecode(img_data, cv2.IMREAD_COLOR)

            # Convert image to display in tkinter
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            img = ImageTk.PhotoImage(img)

            image_label.config(image=img)
            image_label.image = img
        else:
            print("Failed to get a valid response from the server.")
    except Exception as e:
        print("Error:", e)

# Add button to load image
load_button = Button(window, text="Open Image", command=open_image)
load_button.pack()

window.mainloop()
