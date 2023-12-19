import tkinter as tk
import tkinter.messagebox
import tkinter.filedialog as filedialog
import customtkinter as ctk
import requests
from PIL import Image, ImageTk, ImageDraw, ImageOps
from io import BytesIO


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        #0.1 Configuration
        self.title("Funcraft Editor")
        #self.geometry(f"{1000}x{600}") #TODO: Screen size or fullscreen decide
        self.bind("<Escape>", self.toggle_fullscreen)
        self.grid_columnconfigure((0,1,2),  weight=1)
        self.grid_rowconfigure((0,1,2,3), weight=1)
        self.resizable(False, False)
        
        #0.2 Variables
        self.tunnel_url = ctk.StringVar()
        self.guidance_scale = ctk.IntVar()
        self.strength = ctk.DoubleVar()
        self.number_of_steps = ctk.IntVar()
        self.seed = ctk.IntVar()
        self.prompt = ctk.StringVar()
        self.negative_prompt = ctk.StringVar()
        self.is_settings_open = False
        self.is_styles_open = False
        self.is_edit_clicked_box= False
        self.is_edit_clicked_brush= False
        self.genmode_var = tkinter.IntVar(value=0)
        self.help_window = None
        self.help_window_clicked = False

        #image
        self.image= Image.open('Funcraft.png').resize((512,512))
        self.tk_image= ImageTk.PhotoImage(self.image)
        self.generated_images = []  # Initialize the list to store generated images and ImageTk instances
        
        #inpainting box variables 
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0

        #inpainting brush variables
        self.brush_size = 15
        self.brush_color = "#b5a2c8"
        self.draw_state = False
        self.last_x, self.last_y = None, None
        self.current_line = None
        self.undo_stack = []

        #1. Sidebar Frame
        self.sidebar_frame = ctk.CTkFrame(self, border_width=1, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        #self.sidebar_button_1 = ctk.CTkButton(self.sidebar_frame, text='Upload Image', command=self.sidebar_button_event)
        #self.sidebar_button_1.grid(row=1, column=0, padx=20, pady=10)
        
        #1.1. Prompt Label
        self.prompt_entry_label= ctk.CTkLabel(self.sidebar_frame, text='Prompt', font=ctk.CTkFont(size=16))
        self.prompt_entry_label.grid(row=0, column=0, padx=(20, 20), pady=(20,10))
        
        #1.2. Prompt Entry Box
        self.prompt_entry = ctk.CTkTextbox(self.sidebar_frame, width=200, height=120, wrap="word")
        self.prompt_entry.grid(row=1, column=0, padx=(20, 20), pady=(10,10), columnspan=2, sticky="ew")
        self.default_pe_text="Type something.."
        self.prompt_entry.insert("0.0",self.default_pe_text)
        self.prompt_entry.bind("<FocusIn>", self.pe_on_click)
        self.prompt_entry.bind("<FocusOut>", self.pe_on_leave)
        
        #1.3. Negative Prompt Entry Box
        self.negative_prompt_entry = ctk.CTkEntry(self.sidebar_frame, placeholder_text="Negative Prompt")
        self.negative_prompt_entry.grid(row=2, column=0, padx=(20,20), pady=(10,10), sticky="nsew")
        
        #1.4. Styles Button
        self.styles_button = ctk.CTkButton(self.sidebar_frame, width=200, fg_color='#2a2b2b', hover_color='#333333', text_color='#9e9e9e', text='▼ Styles', anchor='w', command=self.toggle_styles)
        self.styles_button.grid(row=3, column=0, padx=(20,20), pady=(10,10), sticky="ew")
        
        #1.5. Settings Button
        self.setting_button = ctk.CTkButton(self.sidebar_frame, width=200, fg_color='#2a2b2b', hover_color='#333333', text_color='#9e9e9e', text='▼ Settings', anchor='w', command=self.toggle_settings)
        self.setting_button.grid(row=5, column=0, padx=(20,20), pady=(10,10), sticky="ew")
        
        #1.6. Variations Checkbox
        self.variations_checkbox = ctk.CTkCheckBox(self.sidebar_frame, text="Variations", text_color='#9e9e9e',
                                     variable=self.genmode_var, onvalue=1, offvalue=0)
        self.variations_checkbox.grid(row=6, column=0, padx=(20, 20), pady=(10, 10), sticky="we")

        #1.7. Generate Button
        self.generate_button = ctk.CTkButton(self.sidebar_frame, text= 'Generate', command=self.gen_button_click)
        self.generate_button.grid(row=7, column=0, columnspan=2, padx=(40, 40), pady=(10, 10), sticky="we")

        #1.8. Colab Connection URL Button
        self.colab_con_button = ctk.CTkButton(self.sidebar_frame, text="Colab Connection URL", command=self.open_input_dialog_event)
        self.colab_con_button.grid(row=8, column=0, columnspan=2, padx=(60,60), pady=(10,20))
        
        #2. Canvas
        self.canvas_frame = ctk.CTkFrame(self, width=512, height=512, fg_color="transparent")
        self.canvas_frame.grid(row=0, column=2, padx=(0, 0), pady=(20, 0), sticky="nsew")
        
        self.canvas = tk.Canvas(self, width=512, height=512, bg='#242424', highlightthickness=0, relief='ridge')
        self.canvas_image_item= self.canvas.create_image(256,256, anchor="center")
        self.canvas.grid(row=0, column=2, padx=(5, 0), pady=(20, 0), sticky="nsew")
        

        #2.1 Canvas Buttons
        self.canvas_button_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        self.import_button_img = ctk.CTkImage(Image.open("buttons/plus.png"), size=(30,30))
        self.import_button = ctk.CTkButton(self.canvas_button_frame, text="", image=self.import_button_img , width=5, height=5, fg_color="transparent", corner_radius=2, border_width=0, border_spacing=0, hover_color='#333333', command=self.import_image)
        self.import_button.grid(row=0, column=0, padx=(10,0), pady=5)

        self.edit_button_img = ctk.CTkImage(Image.open("buttons/edit.png"), size=(30,30))
        self.canvas_edit_button = ctk.CTkButton(self.canvas_button_frame, text="", image=self.edit_button_img , width=5, height=5, fg_color="transparent", corner_radius=2, border_width=0, border_spacing=0, hover_color='#333333', command=self.switch_to_inpainting_box )
        self.canvas_edit_button.grid(row=1, column=0, padx=(10,0), pady=5)

        self.brush_button_img = ctk.CTkImage(Image.open("buttons/brush.png"), size=(30,30))
        self.canvas_brush_button = ctk.CTkButton(self.canvas_button_frame, text="", image=self.brush_button_img , width=5, height=5, fg_color="transparent", corner_radius=2, border_width=0, border_spacing=0,hover_color='#333333', command=self.switch_to_inpainting_brush)
        self.canvas_brush_button.grid(row=2, column=0, padx=(10,0), pady=5)

        self.save_button_img = ctk.CTkImage(Image.open("buttons/save.png"), size=(30,30))
        self.canvas_save_button = ctk.CTkButton(self.canvas_button_frame, text="", image=self.save_button_img , width=5, height=5, fg_color="transparent", corner_radius=2, border_width=0, border_spacing=0,hover_color='#333333', command=self.save_image)
        self.canvas_save_button.grid(row=3, column=0, padx=(10,0), pady=5)
        self.canvas_button_frame.grid(row=0, column=1, sticky="n", pady=20)
   

        #3. History Frame
        self.scrollable_frame = ctk.CTkScrollableFrame(self, label_text="History",height=458)
        self.scrollable_frame.grid(row=0, column=3, padx=(20, 10), pady=(20, 10), sticky="n" )
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        #4. Styles Frame 
        self.styles_frame=ctk.CTkScrollableFrame(self.sidebar_frame, width=340)
        self.selected_style = ctk.StringVar(value="No Style")
        self.thumbnails = {}
        self.style_buttons = []
        images = {}
        image_paths = {
            "No Style": "styles/nostyle.png",
            "Photorealistic": "styles/photorealistic.png",
            "Portrait": "styles/portrait.png",
            "Cyberpunk": "styles/cyberpunk.png",
            "Anime":"styles/anime.png",
            "Cinematography":"styles/Cinematography.png",
            "PixelArt":"styles/PixelArt.png",
            "AnalogFilm":"styles/AnalogFilm.png",
            "Futuristic":"styles/Futuristic.png",
            "Fantasy":"styles/Fantasy.png"
        }
        self.populate_images(images,image_paths)
        self.selected_button = None  # To keep track of the selected button

        #5. Help buttons
        self.help_button_img = ctk.CTkImage(Image.open("buttons/ask.png"), size=(15,15))
        self.neg_prompt_help_button = ctk.CTkButton(self.sidebar_frame, text="", image=self.help_button_img, width=5, height=5, fg_color="transparent", 
                                                    corner_radius=2, border_width=0, border_spacing=0, hover_color='#333333', command= lambda: self.show_help("Negative Prompt"))
        self.neg_prompt_help_button.grid(row=2, column=1, padx=(10,10), pady=0)
        
        self.settings_help_button = ctk.CTkButton(self.sidebar_frame, text="", image=self.help_button_img , width=5, height=5, fg_color="transparent",         
                                            corner_radius=2, border_width=0, border_spacing=0, hover_color='#333333', command= lambda: self.show_help("Settings"))
        self.settings_help_button.grid(row=5, column=1, padx=(10,10), pady=0)
        
        self.settings_help_button = ctk.CTkButton(self.sidebar_frame, text="", image=self.help_button_img , width=5, height=5, fg_color="transparent",         
                                            corner_radius=2, border_width=0, border_spacing=0, hover_color='#333333', command= lambda: self.show_help("Variations"))
        self.settings_help_button.grid(row=6, column=1, padx=(10,10), pady=0)


        #6. Settings Frame
        self.settings_frame = ctk.CTkFrame(self.sidebar_frame, width=200)
           
        self.guidance_scale_label = ctk.CTkLabel(self.settings_frame, text='Guidance Scale:')
        self.guidance_scale_label.grid(row=1, column=0, padx=(20, 10), sticky="w")
        self.guidance_scale_slider = ctk.CTkSlider(self.settings_frame, from_=0, to=2,  variable=self.guidance_scale)
        self.guidance_scale_slider.grid(row=2, column=0, padx=(20, 10), sticky="ew")
        self.guidance_scale_value_label= ctk.CTkLabel(self.settings_frame, text=f'{self.guidance_scale.get()}')
        self.guidance_scale_value_label.grid(row=2, column=1, padx=(20, 20), sticky="w")
        def update_guidance_scale_value_label(*args): #TODO Functions to the bottom of the code
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
        self.steps_slider = ctk.CTkSlider(self.settings_frame, from_=1, to=10, variable=self.number_of_steps)
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
        self.set_default_settings()

    def set_default_settings(self):
        self.canvas.itemconfig(self.canvas_image_item, image=self.tk_image)
        self.guidance_scale.set(1)
        self.strength.set(0.6)
        self.number_of_steps.set(4)
        self.seed.set(0)
        self.image.save('selected_image.png') #initial selected image is the main page image
        
    def populate_images(self, images, image_paths):
        row_c=0
        column_c=0
        counter=1
        for option, path in image_paths.items():
            image = Image.open(path)
            image = image.resize((64, 64))
            images[option] = image
            thumbnail = ImageTk.PhotoImage(image)
            self.thumbnails[option] = thumbnail

            # Create a new button for each style
            style_button = ctk.CTkButton(self.styles_frame, text=option, image=thumbnail, cursor='hand',
                                         compound="top", width=100, height=100, fg_color="#333333",
                                         hover_color="#3b3b3b", command=lambda option=option: self.select_style(option))
            self.style_buttons.append(style_button)  # Store the Button instance
            style_button.grid(row=row_c, column=column_c, padx=5, pady=5)
            column_c+=1
            if column_c == 3:
                column_c = 0
                row_c += 1
            counter+=1


    def open_input_dialog_event(self):
        dialog = ctk.CTkInputDialog(text="Type in the URL:", title="Colab Tunnel URL")
        self.tunnel_url.set(dialog.get_input())
        print("Collab Connection URL:", self.tunnel_url.get())

    def create_help_content(self, help_text="Negative Prompt"):
    #lculate the position for the help window
        x, y, _, _ = self.bbox("current")
        x_root = self.winfo_rootx()
        y_root = self.winfo_rooty()
        x_offset = 300  # You can adjust this offset as needed
        y_offset = 300
        self.help_window = ctk.CTkToplevel(self)
        #self.help_window.geometry("400x200+700+600")
        self.help_window.geometry(f"+{x_root + x + x_offset}+{y_root + y + y_offset}")
        self.help_window.resizable(False,False)
        self.help_window.title("Help")
        self.neg_prompt_help_text = "A negative prompt in image generation refers to input instructions that specify what should not be present in the generated image. It guides the model by highlighting elements or features to be avoided, helping shape the output by excluding undesired content."
        self.settings_help_text = """Guidance Scale:
- Description: Adjusts the strength of external guidance in the diffusion process.
- Use Case: Higher values prioritize external guidance, influencing the generated image more significantly.


Strength:
- Description: Controls the intensity of the image generation process.
- Use Case: Higher strength values result in more pronounced changes during diffusion, affecting image details.


Number of Steps:
- Description: Specifies the number of iterations or steps in the diffusion or inpainting process.
- Use Case: Increasing steps can refine details but may extend processing time. Find a balance for optimal results.
"""


        self.variations_help_text = """- Description: Sends the image to image-to-image pipeline, allowing creative outputs using reference.
- Use Case: When checked, introduces diversity in the generated images using canvas image as reference. Used for more creative and varied results. Can be tuned using settings.
"""
        self.help_dict = {}
        self.help_dict["Negative Prompt"]= self.neg_prompt_help_text
        self.help_dict["Settings"]= self.settings_help_text
        self.help_dict["Variations"]= self.variations_help_text


        # Display help text
        help_label = ctk.CTkLabel(self.help_window, text=help_text, padx=20, pady=10)
        help_label.pack()     
        help_textbox = ctk.CTkTextbox(self.help_window, width=400, height=100, wrap="word", state="normal")
        help_textbox.insert("0.0", self.help_dict[help_text])
        help_textbox.configure(state="disabled")
        help_textbox.pack(padx=(10,10), pady=10)
        
    
    
    def show_help(self, help_text):
            if self.help_window is None or not self.help_window.winfo_exists():
                self.create_help_content(help_text=help_text)
            else:
                self.help_window.destroy()
                self.create_help_content(help_text=help_text)


    

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)
    
    def toggle_styles(self):
        if self.is_settings_open==True:
            self.settings_frame.grid_forget()
            self.is_settings_open = False

        if self.is_styles_open == False:
            self.styles_frame.grid(row=4, column=0, columnspan=2, padx=(20, 20), pady=(10,10))
            self.is_styles_open = True
        else:
            self.styles_frame.grid_forget()
            self.is_styles_open = False
    
    def toggle_settings(self):
        if self.is_styles_open==True:
            self.styles_frame.grid_forget()
            self.is_styles_open = False

        if self.is_settings_open == False:
            self.settings_frame.grid(row=6, column=0, columnspan=2, padx=(20, 20), pady=(10,10))
            self.is_settings_open = True

        else:
            self.settings_frame.grid_forget()
            self.is_settings_open = False

    #brush functions

    def start_brush(self, event):
        self.last_x, self.last_y = event.x, event.y
        self.draw_state = True
        self.current_line = self.canvas.create_line(event.x, event.y, event.x, event.y,
                                                    width=self.brush_size, fill=self.brush_color,
                                                    capstyle=tk.ROUND, smooth=tk.TRUE, tags="brush")

    def draw_brush(self, event):
        if self.draw_state:
            if self.last_x and self.last_y:
                new_x, new_y = event.x, event.y
                self.canvas.create_line(self.last_x, self.last_y, new_x, new_y,
                                        width=self.brush_size, fill=self.brush_color,
                                        capstyle=tk.ROUND, smooth=tk.TRUE, tags="brush")
                self.mask_draw.line([self.last_x, self.last_y, new_x, new_y], fill=255, width=self.brush_size)
                self.last_x, self.last_y = new_x, new_y

    def stop_brush(self, event):
        self.draw_state = False
        self.last_x, self.last_y = None, None
        if self.current_line:
            self.undo_stack.append(self.current_line)
    
    def undo(self, event):
        if self.undo_stack:
            item = self.undo_stack.pop()
            self.canvas.delete(item)
            # Update the mask when undoing
            self.mask_image = Image.new("L", (512, 512), color=0)
            self.mask_draw = ImageDraw.Draw(self.mask_image)
            for line_item in self.undo_stack:
                line_coords = self.canvas.coords(line_item)
                self.mask_draw.line(line_coords[0:4], fill=255, width=self.brush_size)



    def canvas_brush_key_binds(self):
        self.canvas.bind("<Button-1>", self.start_brush)
        self.canvas.bind("<B1-Motion>", self.draw_brush)
        self.canvas.bind("<ButtonRelease-1>", self.stop_brush)
        self.canvas.bind("<Control-z>", self.undo)


    def switch_to_inpainting_brush(self):
        if self.is_edit_clicked_box==True:
            self.canvas_edit_button.configure(border_width=0)
            self.canvas.delete("box")
            self.is_edit_clicked_box=False

        if self.is_edit_clicked_brush== False:
            self.genmode_var.set(2)
            self.canvas_brush_button.configure(border_width=1, border_color="#b5a2c8" )
            self.mask_image = Image.new("L", (512, 512), color=0)
            self.mask_draw = ImageDraw.Draw(self.mask_image)
            self.canvas_brush_key_binds()
            self.is_edit_clicked_brush=True
        else:
            self.genmode_var.set(0)
            self.canvas_brush_button.configure(border_width=0)
            self.is_edit_clicked_brush=False
            self.canvas.delete("brush")



    def toggle_fullscreen(self, event):
        self.attributes("-fullscreen", False)

    def sidebar_button_event(self):
        print("sidebar_button click")

    #create box functions
    def on_button_press(self, event):
        if self.is_edit_clicked_box==True:
            self.start_x = event.x
            self.start_y = event.y

    def on_button_motion(self, event):
        if self.is_edit_clicked_box==True:
            # Update the box as the mouse is moved
            self.canvas.delete("box")
            self.end_x = event.x
            self.end_y = event.y
            self.canvas.create_rectangle(self.start_x, self.start_y, self.end_x, self.end_y, outline="red", tags="box")

    def on_button_release(self, event):
        if self.is_edit_clicked_box==True:
            # Update the box when the mouse button is released
            self.end_x = event.x
            self.end_y = event.y
            self.canvas.create_rectangle(self.start_x, self.start_y, self.end_x, self.end_y, outline="red", tags="box")
    
    def canvas_edit_box_key_binds(self):
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_button_motion)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

    def switch_to_inpainting_box(self):
        if self.is_edit_clicked_brush==True:
            self.canvas_brush_button.configure(border_width=0)
            self.canvas.delete("brush")
            self.is_edit_clicked_brush=False

        if self.is_edit_clicked_box== False:
            self.genmode_var.set(2)
            self.canvas_edit_button.configure(border_width=1, border_color="#b5a2c8" )
            self.canvas_edit_box_key_binds()
            self.is_edit_clicked_box=True
        else:
            self.genmode_var.set(0)
            self.canvas_edit_button.configure(border_width=0)
            self.canvas.delete("box")
            self.is_edit_clicked_box=False


    #default text is removed when the user clicks on the text entry box
    def pe_on_click(self, event):
        if self.prompt_entry.get("1.0", "end-1c") == self.default_pe_text :
           self.prompt_entry.delete("1.0", "end")
           
    #prompt entry
    def pe_on_leave(self, event):
        if not self.prompt_entry.get("1.0", "end-1c"):
            self.prompt_entry.insert("1.0", self.default_pe_text)

    def select_style(self, option):
        # Reset the border for previously selected button
        if self.selected_button:
            self.selected_button.configure(border_width=0)

        # Find the selected button based on the clicked option
        for button in self.style_buttons:
            if button.cget("text") == option:
                # Set a border for the selected button
                button.configure(border_width=2, border_color="#b5a2c8")
                self.selected_button = button
                self.selected_style.set(option)
                break

        print(f'selected style is: {self.selected_style.get()}')



    def save_image(self):
        
        save_image_file = filedialog.asksaveasfilename(defaultextension=".png",
                                                filetypes=[("PNG files", "*.png"), ("All Files", "*.*")])
        
        if save_image_file:
            img=Image.open("selected_image.png")
            img.save(save_image_file,'png')
            print(f"Image saved as {save_image_file}")

    def import_image(self):
        
        file_path = filedialog.askopenfilename(
            initialdir="/", title="Select Image", filetypes=[("PNG files", "*.png"), ("All Files", "*.*")]
        )

        if file_path:
            # Open the selected image file
            imported_image = Image.open(file_path)

            # Resize the image to (512, 512)
            resized_imported_image = imported_image.resize((512, 512))

            resized_imported_image.save('selected_image.png')
            self.imported_image_tk = ImageTk.PhotoImage(resized_imported_image)
            self.canvas.itemconfig(self.canvas_image_item, image=self.imported_image_tk)
            self.canvas.image = self.imported_image_tk



    def gen_button_click(self):
        print('\nGen button clicked')
        print(f'Gen mode: {self.genmode_var.get()}')
        print(f'Guidance scale: {self.guidance_scale.get()}')
        print(f'strength scale: {self.strength.get()}')
        print(f'Number of steps: {self.number_of_steps.get()}')
        print(f'Image size:{self.image.size}')
        print(f"Selected style:{self.selected_style.get()}")
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
        'negative_prompt': self.negative_prompt,
        'selected_style': self.selected_style.get()
        }
        
        self.canvas.delete("box")
        self.canvas.delete("brush")
        
        #text to image
        if self.genmode_var.get()==0:
        
            
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
        if self.is_edit_clicked_box==True :
            self.mask_image = Image.new('L', (512,512))
            draw = ImageDraw.Draw(self.mask_image)
            draw.rectangle([self.start_x, self.start_y, self.end_x, self.end_y], fill=255)
            #self.mask_image.show()
            print('Mask image created successfully!')

        if self.is_edit_clicked_brush== True:
            #self.mask_image.show()
            print('Mask image created successfully!')
        
        
        if self.genmode_var.get()==2:
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
            self.processed_image.save('selected_image.png')

            self.resized_canvas_processed_image_tk = ImageTk.PhotoImage(self.processed_image.resize((512, 512)))
            self.canvas.itemconfig(self.canvas_image_item, image=self.resized_canvas_processed_image_tk)
            self.canvas.image = self.resized_canvas_processed_image_tk  # Keep a reference to avoid garbage collection


            # Resize the processed image to the desired size for scrollable history frame
            self.resized_processed_image_tk = ImageTk.PhotoImage(self.processed_image.resize((128, 128)))  # Adjust the size as needed
            
            # Store the generated image and its corresponding ImageTk.PhotoImage instance
            self.generated_images.append((self.processed_image, self.resized_processed_image_tk))

            # Clear the contents of the scrollable frame
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
                

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
