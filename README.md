# funcraft

- [Introduction](#introduction)
- [Highlights](#highlights)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Intro
Funcraft stands as an AI-driven solution for photo editing enthusiasts. By harnessing the capabilities of the SDXL 1.0 diffuser model, Funcraft delivers powerful image manipulation possibilities. The frontend GUI offers a seamless way to interact with custom-tuned pipelines, enabling users to elevate their images with ease.

## Highlights
- Leverage the SDXL 1.0 diffuser model for advanced image editing.
- Perform tasks like text-to-image conversion, image-to-image transformations, and inpainting.
- Optimize GPU memory usage through the diffuser pipeline inheritance feature.
- Completely free to use, ensuring accessibility to all users.
- No need for a high-performance local GPU; the backend utilizes Google Colab's T4 GPU for processing.
- The average image generation time is 45 seconds at the free tier collab.

## Features
- **Text-to-Image:** Transform text inputs into compelling images with just a few clicks.
- **Image-to-Image:** Harness the power of image-to-image transformations to give your pictures a fresh perspective.
- **Inpainting:** Seamlessly remove unwanted elements from your images with the inpainting pipeline.

  
## Installation

1. **Prerequisites:**
   - Make sure you have [pip](https://pip.pypa.io/en/stable/installing/) installed.
   - Make sure you have [Git](https://git-scm.com/downloads) installed.
   - Ensure you have [Python](https://www.python.org/downloads/) installed (requires Python >=3.7.).

2. Open your terminal(MAC)/command-prompt(windows) and execute the following commands.
3. Clone this repository: `git clone https://github.com/efecte8/funcraft.git`
4. Navigate to the project directory: `cd funcraft`
5. Install the dependencies: `pip install -r requirements.txt`
6. Launch the Funcraft GUI: `python funcraft_gui.py`
7. ***At the collab*** run the first cell of the notebook. Wait for the dependencies to be installed (takes 2mins), it will restart the runtime at the end.
8. ***At the collab*** Run the remaining cells and at the end of the last cell, you will be given a ngrok URL (_running on_) that will tunnel the collab to the GUI. Copy that URL.
9. Click the collab URL button at the GUI and paste the URL.
10. Enjoy!

## Usage
1. Launch the Funcraft GUI by running the desktop app.
3. Choose from the available pipelines: Text-to-Image, Image-to-Image, or Inpainting.
4. Follow the intuitive interface to customize and process your images.
5. Sit back and let Funcraft's AI-powered capabilities enhance your visuals.

## Contributing
We welcome contributions from the open-source community! If you're interested in improving Funcraft, follow these steps:
1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Commit your changes and push them to your fork.
4. Submit a pull request, and we'll review your contribution.

## License
This project is licensed under the [MIT License](LICENSE.txt).

---

*Disclaimer: This project is not affiliated with or endorsed by Google Collab or the creators of the SDXL 1.0 diffuser model.*

