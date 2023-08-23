# funcraft

## Intro
Funcraft is a free AI photo editing tool that runs the open-source SDXL 1.0 diffuser model at the backend. The GUI runs locally as a desktop app and allows users to interact with the custom-tuned pipelines of the model. The backend runs on Google Collab and utilizes the free T4 GPU. The backend also includes a Flask web app framework to connect with the GUI.

The average image generation time is 45 seconds at the free tier collab.

## Highlights
- Includes text to image, image to image, and inpainting pipelines.
- SDXL 1.0 base model components are reused in different pipelines by utilizing the diffuser pipeline inheritance feature, which allows GPU memory optimization.
- It's completely free.
- No need to have a strong local GPU.
  
## Installation steps
### Local:
1. Make sure you have pip installed
2. Make sure you have Python installed (the current version runs with Python 3.10)
3. Git clone the repo
4. Open your terminal and install the requirements to your environment with the command: pip install -r requirements.txt 

### Collabside funcraft_backend:
5. Run the first cell of the notebook. Wait for the dependencies to be installed (takes 2mins), it will restart the runtime at the end.
6. Run the remaining cells and at the end of the last cell, you will be given a ngrok URL that will tunnel the collab to the GUI. Copy that url.

### Lastly at the GUI 
7. Run the gui from your terminal with the command: python funcraft_gui.py
8. Click the collab url button at the GUI and paste the URL.
9. Enjoy!


