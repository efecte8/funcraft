import tkinter as tk
import tkinter.messagebox
import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw
import requests
from io import BytesIO

ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # configure window
        self.title("Funcraft Editor")
        #self.geometry(f"{1000}x{960}")
        self.bind("<Escape>", self.toggle_fullscreen)

        
        #image
        self.image= Image.open('Funcraft.png')
        self.tk_image= ImageTk.PhotoImage(self.image.resize((512,512)))
        self.generated_images = []  # Initialize the list to store generated images and ImageTk instances

        #tunnel url
        self.tunnel_url=ctk.StringVar()

        #variables
        self.guidance_scale= ctk.IntVar()
        self.strength = ctk.DoubleVar()
        self.number_of_steps = ctk.IntVar()
        self.seed= ctk.IntVar()
        self.prompt = ctk.StringVar()
        self.negative_prompt= ctk.StringVar()

        # Variables to store the coordinates of the drawn box
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0

        
        # configure grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2,  weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        # create sidebar frame with widgets
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Funcraft", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.sidebar_button_1 = ctk.CTkButton(self.sidebar_frame, text='Upload Image', command=self.sidebar_button_event)
        self.sidebar_button_1.grid(row=1, column=0, padx=20, pady=10)
        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor='s')
        self.appearance_mode_label.grid(row=3, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode_event, anchor='nw')
        self.appearance_mode_optionemenu.grid(row=4, column=0, padx=20, pady=(10, 0))

        #collab connection url entry
        self.collab_con_button = ctk.CTkButton(self.sidebar_frame, text="Collab Connection URL",
                                                           command=self.open_input_dialog_event)
        self.collab_con_button.grid(row=5, column=0, padx=20, pady=(40))
        

        # prompt entry frame
        self.prompt_entry_frame = ctk.CTkFrame(self)
        self.prompt_entry_frame.grid_columnconfigure(0, weight=1)
        self.prompt_entry_frame.grid(row=1, column=1, padx=(20, 0), pady=10, sticky="nsew") 
        
        self.prompt_entry_label= ctk.CTkLabel(self.prompt_entry_frame, text='Prompt', font=ctk.CTkFont(size=16, weight="bold"))
        self.prompt_entry_label.grid(row=0, column=0, padx=(20, 10), pady=5)
        
        self.prompt_entry = ctk.CTkTextbox(self.prompt_entry_frame)
        self.prompt_entry.grid(row=1, column=0, padx=(20, 10), pady=(20,10), sticky="nsew")
        self.default_pe_text="Enter your prompt here..."
        self.prompt_entry.insert("0.0",self.default_pe_text)
        self.prompt_entry.bind("<FocusIn>", self.pe_on_click)
        self.prompt_entry.bind("<FocusOut>", self.pe_on_leave)


        self.negative_prompt_entry = ctk.CTkEntry(self.prompt_entry_frame, placeholder_text="Negative Prompt")
        self.negative_prompt_entry.grid(row=2, column=0, padx=(20, 10), pady=20, sticky="nsew")
        
        # generate button
        self.generate_button = ctk.CTkButton(master=self, text= 'Generate', fg_color="orange", border_width=2, text_color=("gray10", "gray10"), height=50, command=self.gen_button_click)
        self.generate_button.grid(row=3, column=2, padx=(20, 20), pady=(20, 20), sticky="we")

        # create canvas
        self.canvas = tk.Canvas(self, width=512, height=512, bg='#242424', highlightthickness=0, relief='ridge')
        self.canvas_image_item= self.canvas.create_image(0,0, anchor='nw')
        self.canvas.grid(row=0, column=1, padx=(20, 0), pady=(20, 0), sticky="nsew")

        # Canvas event bindings
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_button_motion)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        # Gen mode frame
        self.radiobutton_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.radiobutton_frame.grid(row=1, column=2, padx=(20, 20), pady=(10, 0), sticky="nw")
        self.genmode_var = tkinter.IntVar(value=0)
        self.label_radio_group = ctk.CTkLabel(master=self.radiobutton_frame, text="Gen Mode:", font=ctk.CTkFont(size=16, weight="bold"))
        self.label_radio_group.grid(row=0, column=2, columnspan=1, padx=10,  sticky="nsew")
        self.text_to_image_button = ctk.CTkRadioButton(master=self.radiobutton_frame, text= 'Text to Image' ,variable=self.genmode_var, value=0)
        self.text_to_image_button.grid(row=1, column=2, pady=5, padx=20, sticky="nw")
        self.image_to_image_button = ctk.CTkRadioButton(master=self.radiobutton_frame, text= 'Image to Image', variable=self.genmode_var, value=1)
        self.image_to_image_button.grid(row=2, column=2, pady=5, padx=20, sticky="nw")
        self.inpainting_button = ctk.CTkRadioButton(master=self.radiobutton_frame, text= 'Inpainting', variable=self.genmode_var, value=2)
        self.inpainting_button.grid(row=3, column=2, pady=5, padx=20, sticky="nw")

        #middle button frame
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.grid(row=3, column=1, padx=(20, 20), pady=(20, 20))
        self.setting_button = ctk.CTkButton(self.button_frame, text='Settings', command=self.settings_pop)
        self.setting_button.grid(column=0, row=0, pady=10, padx=10)
        self.styles_button = ctk.CTkButton(self.button_frame, text='Styles', command=self.styles_pop)
        self.styles_button.grid(column=1, row=0, pady=10, padx=10)

        # styles frame 
        self.styles_frame=ctk.CTkScrollableFrame(self, width=256, label_text='Styles')
        


        # settings frame
        self.settings_frame = ctk.CTkFrame(self,  width=256)
        self.settings_frame.grid_columnconfigure(0, weight=1)
        self.settings_label = ctk.CTkLabel(self.settings_frame, text='Settings', font=ctk.CTkFont(size=12, weight="bold"))
        self.settings_label.grid(row=0, columnspan=2, padx=(20, 10), pady=(10,0))        
        self.guidance_scale_label = ctk.CTkLabel(self.settings_frame, text='Guidance Scale:')
        self.guidance_scale_label.grid(row=1, column=0, padx=(20, 10), sticky="w")
        self.guidance_scale_slider = ctk.CTkSlider(self.settings_frame, from_=5, to=12, variable=self.guidance_scale)
        self.guidance_scale_slider.grid(row=2, column=0, padx=(20, 10), sticky="ew")
        self.guidance_scale_value_label= ctk.CTkLabel(self.settings_frame, text=f'{self.guidance_scale.get()}')
        self.guidance_scale_value_label.grid(row=2, column=1, padx=(20, 20), sticky="w")
        def update_guidance_scale_value_label(*args):
            self.guidance_scale_value_label.configure(text=f'{self.guidance_scale.get()}')
        self.guidance_scale.trace_add('write',update_guidance_scale_value_label)
        self.strength_label=ctk.CTkLabel(self.settings_frame, text='Strength:')
        self.strength_label.grid(row=3, column=0, padx=20, sticky='w')
        self.strength_slider = ctk.CTkSlider(self.settings_frame, from_=0, to=1, number_of_steps=10, variable=self.strength)
        self.strength_slider.grid(row=4, column=0, padx=(20, 10), sticky="ew")
        self.strength_value_label= ctk.CTkLabel(self.settings_frame, text=f'{round(self.strength.get(),1)}')
        self.strength_value_label.grid(row=4, column=1, padx=(20, 20), sticky="w")
        def update_strength_value_label(*args):
            self.strength_value_label.configure(text=f'{round(self.strength.get(),2)}')
        self.strength.trace_add('write',update_strength_value_label)
            
        self.steps_label=ctk.CTkLabel(self.settings_frame, text='Number of steps:')
        self.steps_label.grid(row=5, column=0, padx=(20, 10), sticky='w')
        self.steps_slider = ctk.CTkSlider(self.settings_frame, from_=10, to=100, variable=self.number_of_steps)
        self.steps_slider.grid(row=6, column=0, padx=(20, 10),  sticky="ew")
        self.steps_value_label= ctk.CTkLabel(self.settings_frame, text=f'{self.number_of_steps.get()}')
        self.steps_value_label.grid(row=6, column=1, padx=(20, 20), sticky="w")
        def update_steps_value_label(*args):
            self.steps_value_label.configure(text=f'{self.number_of_steps.get()}')
        self.number_of_steps.trace_add('write',update_steps_value_label)
    
        self.seed_label = ctk.CTkLabel(self.settings_frame, text='Seed:')
        self.seed_label.grid(row=7, column=0, padx=(20, 10), sticky='w')
        self.seed_entry = ctk.CTkEntry(self.settings_frame, placeholder_text="Set to random", width=100)
        self.seed_entry.grid(row=8, column=0, padx=(20, 10), pady=(0,20), sticky="w")
        self.settings_close_button = ctk.CTkButton(self.settings_frame, text= 'Save&Close', fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"), height=25, anchor='center', command=self.close_settings)
        self.settings_close_button.grid(row=9, columnspan=3, padx=(20, 20), pady=(20, 20) ,sticky='we')
        #self.progressbar_1 = ctk.CTkProgressBar(self.settings_frame)
        #self.progressbar_1.grid(row=1, column=0, padx=(20, 10), pady=(10, 10), sticky="ew")

        # create history frame
        self.scrollable_frame = ctk.CTkScrollableFrame(self, label_text="History")
        self.scrollable_frame.grid(row=0, column=2, padx=(20, 10), pady=(20, 0), sticky="nsew")
        self.scrollable_frame.grid_columnconfigure(0, weight=1)



        # set default values
        self.canvas.itemconfig(self.canvas_image_item, image=self.tk_image)
        self.guidance_scale.set(7)
        self.strength.set(0.6)
        self.number_of_steps.set(50)
        self.seed.set(0)
        self.image.save('selected_image.png') #initial selected image is the main page image
        #self.inpainting_button.configure(state="disabled")
        self.appearance_mode_optionemenu.set("Dark")
        

    def open_input_dialog_event(self):
        dialog = ctk.CTkInputDialog(text="Type in the URL:", title="Collab Tunnel URL")
        self.tunnel_url.set(dialog.get_input())
        print("Collab Connection URL:", self.tunnel_url.get())

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)
    
    def settings_pop(self):
        self.styles_frame.grid_forget()
        self.settings_frame.grid(column=3, row=0, rowspan=4, padx=(10, 10), pady=(20, 20), sticky="nsew")

    def styles_pop(self):
        self.settings_frame.grid_forget()
        self.styles_frame.grid(column=3, row=0, rowspan=4, padx=(10, 10), pady=(20, 20), sticky="nsew")

    def close_settings(self):
        self.settings_frame.grid_forget()

    def toggle_fullscreen(self, event):
        self.attributes("-fullscreen", False)

    def sidebar_button_event(self):
        print("sidebar_button click")

    def on_button_press(self, event):
        if self.genmode_var.get() ==2:
            self.start_x = event.x
            self.start_y = event.y

    def on_button_motion(self, event):
        if self.genmode_var.get() ==2:
            # Update the box as the mouse is moved
            self.canvas.delete("box")
            self.end_x = event.x
            self.end_y = event.y
            self.canvas.create_rectangle(self.start_x, self.start_y, self.end_x, self.end_y, outline="red", tags="box")

    def on_button_release(self, event):
        if self.genmode_var.get() ==2:
            # Update the box when the mouse button is released
            self.end_x = event.x
            self.end_y = event.y
            self.canvas.create_rectangle(self.start_x, self.start_y, self.end_x, self.end_y, outline="red", tags="box")

    
    #default text is removed when the user clicks on the text entry box
    def pe_on_click(self, event):
        if self.prompt_entry.get("1.0", "end-1c") == self.default_pe_text :
           self.prompt_entry.delete("1.0", "end")
           

    def pe_on_leave(self, event):
        if not self.prompt_entry.get("1.0", "end-1c"):
            self.prompt_entry.insert("1.0", self.default_pe_text)


    def gen_button_click(self):
        print('\nGen button clicked')
        print(f'Gen mode: {self.genmode_var.get()}')
        print(f'Guidance scale: {self.guidance_scale.get()}')
        print(f'strength scale: {self.strength.get()}')
        print(f'Number of steps: {self.number_of_steps.get()}')
        print(f'Image size:{self.image.size}')
        try:
            self.seed = int(self.seed_entry.get())
        except ValueError:
            self.seed = 0
        print(f'Seed:{self.seed}')
        self.prompt=self.prompt_entry.get("1.0", "end-1c")
        self.negative_prompt=self.negative_prompt_entry.get()
        print(f'prompt: {self.prompt}')
        print(f'Negative prompt: {self.negative_prompt}')
        
        # Prepare data to send in the POST request
        data = {
        'gen_mode': self.genmode_var.get(),
        'guidance_scale': self.guidance_scale.get(),
        'strength_scale': self.strength.get(),
        'number_of_steps': self.number_of_steps.get(),
        'seed': self.seed,
        'prompt': self.prompt,
        'negative_prompt': self.negative_prompt
        }
        
        self.canvas.delete("box")
        
        #text to image
        if self.genmode_var.get()==0:
        
            # Include the image and mask image files in the files parameter
            files = {}
            url = self.tunnel_url.get() + '/texttoimage'

        #imagetoimage
        if self.genmode_var.get()==1:
            self.image_file = open('selected_image.png', 'rb')
            # Include the image
            files = {
            'image': ('image.png', self.image_file)
            }
            url = self.tunnel_url.get() + '/imagetoimage'

        #inpainting
        if self.genmode_var.get()==2:
            self.mask_image = Image.new('L', (512,512))
            draw = ImageDraw.Draw(self.mask_image)
            draw.rectangle([self.start_x, self.start_y, self.end_x, self.end_y], fill=255)
            print('Mask image created successfully!')
        
            # Prepare the image and mask image files
            self.image_file = open('selected_image.png', 'rb')  # Change the path accordingly
            self.mask_image_resized= self.mask_image.resize(self.image.size)
            print(f'mask image size:{self.mask_image_resized.size}')
            self.mask_image_resized.save('mask_image.png')
            self.mask_image_file = open('mask_image.png', 'rb')  # Change the path accordingly

            # Include the image and mask image files in the files parameter
            files = {
            'image': ('image.png', self.image_file),
            'mask_image': ('mask_image.png', self.mask_image_file)
            }

            url = self.tunnel_url.get() + '/inpainting'
        


        # Make a POST request to your backend
        response = requests.post(url, data=data, files=files)
        
        # Check the response from the backend
        if response.status_code == 200:
            print('POST request successful')
            # Get the processed image from the response
            processed_image_bytes = response.content
            self.processed_image = Image.open(BytesIO(processed_image_bytes))
            self.processed_image.save('gen_image1.png')

            # Resize the processed image to the desired size
            self.resized_processed_image_tk = ImageTk.PhotoImage(self.processed_image.resize((128, 128)))  # Adjust the size as needed
            
            # Store the generated image and its corresponding ImageTk.PhotoImage instance
            self.generated_images.append((self.processed_image, self.resized_processed_image_tk))

            # Clear the contents of the scrollable frame
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
                print('scrollable frame cleared')

            for index, (processed_image, resized_processed_image_tk) in enumerate(self.generated_images):
            # Display the resized image in the scrollable frame
                self.resized_image_label = tk.Label(self.scrollable_frame, image=resized_processed_image_tk)
                self.resized_image_label.pack(pady=10)

                # Bind a click event to the resized image label
                self.resized_image_label.bind("<Button-1>", lambda event, index=index: self.select_image(index))


        else:
            print(f'POST request failed with status code: {response.status_code}')

    def select_image(self, index):
        selected_image, _ = self.generated_images[index]  # Get the selected generated image
        selected_image.save('selected_image.png')
        selected_image_tk = ImageTk.PhotoImage(selected_image.resize((512, 512)))
        self.canvas.itemconfig(self.canvas_image_item, image=selected_image_tk)
        self.canvas.image = selected_image_tk  # Keep a reference to avoid garbage collection

if __name__ == "__main__":
    app = App()
    app.mainloop()
