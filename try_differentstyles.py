input_prompt= 'a woman drinking a glass of wine'
input_neg_prompt='low quality'

style_dictionary = {

       "Photorealistic": {
        "prompt": ", photorealistic, dslr,  intricate, elegant, highly detailed, 8k, sharp focus, 35mm photograph, film, bokeh, professional, 4k",
        "neg_prompt": "drawing, painting, crayon, sketch, graphite, impressionist, noisy, blurry, soft, deformed, ugly"
    },


        "Photorealistic2": {
        "prompt": "breathtaking {prompt}. award-winning, professional, highly detailed",
        "neg_prompt": "anime, cartoon, graphic, text, painting, crayon, graphite, abstract glitch, blurry"
    },


        "Analog Film": {
        "prompt": ", analog film photo {prompt}. faded film, desaturated, 35mm photo, grainy, vignette, vintage, Kodachrome, Lomography, stained, highly detailed, found footage",
        "neg_prompt": "painting, drawing, illustration, glitch, deformed, mutated, cross-eyed, ugly, disfigured"
    },


        "Portrait": {
        "prompt": ", model shot, beautiful detailed eyes, professional award winning portrait photography, Zeiss 150mm f/2.8, highly detailed glossy eyes, high detailed skin, skin pores",
        "neg_prompt": "painting, drawing, illustration, glitch, deformed, mutated, cross-eyed, ugly, disfigured"
    },


       "Portrait unconventional": {
        "prompt": "portrait of {prompt} in style of Marcin Nagreba and Tim Flach, out of focus geometric shapes flying around, inside a futuristic building as background, dark cyan and orange tones and dramatic light, no text, sharp focus, editorial portrait",
        "neg_prompt": "painting, glitch, deformed, mutated, cross-eyed, disfigured, low quality"
    },


        "Futuristic Painting": {
        "prompt": ", futuristic, inspired by Krenz Cushart, neoism, kawacy, wlop, gits anime",
        "neg_prompt": ""
    },

         "Digital painting artwork": {
        "prompt": ", digital artwork, illustrative, painterly, matte painting, highly detailed, cinematic composition",
        "neg_prompt": "photo, photorealistic, realism, ugly"
    },

        "Digital painting Mixed Media": {
        "prompt": ", a digital painting, by Jason Benjamin, shutterstock, colorful vector illustration, mixed media style illustration, epic full color illustration, mascot illustration",
        "neg_prompt": ""
    },


       "Cyberpunk": {
        "prompt": ", looking at the camera, cyberpunk art, neo-figurative",
        "neg_prompt": ""
    },


       "Cyberpunk2": {
        "prompt": ", cyberpunk art, inspired by Victor Mosquera, conceptual art, style of raymond swanland, yume nikki, restrained",
        "neg_prompt": ""
    },


        "Highly detailed illustration": {
        "prompt": ",inspired by Cyril Rolando, shutterstock, highly detailed illustration, full color illustration, very detailed illustration, dan mumford and alex grey style",
        "neg_prompt": ""
    },

        "Chinese Painting": {
        "prompt": ", a fine art painting, by Qiu Ying, no gradients, flowing sakura silk, beautiful oil painting",
        "neg_prompt": ""
    },

        "Anime": {
        "prompt": "anime artwork {prompt}. anime style, key visual, vibrant, studio anime, highly detailed",
        "neg_prompt": "photo, deformed, black and white, realism, disfigured, low contrast"
    },

        "Ethereal Fantasy Art": {
        "prompt": "ethereal fantasy concept art of {prompt}. magnificent, celestial, ethereal, painterly, epic, majestic, magical, fantasy art, cover art, dreamy",
        "neg_prompt": "photographic, realistic, realism, 35mm film, dslr, cropped, frame, text, deformed, glitch, noise, noisy, off-center, deformed, cross-eyed, closed eyes, bad anatomy, ugly, disfigured, sloppy, duplicate, mutated, black and white"
    },


        "Cinematography": {
        "prompt": "cinematic film still {prompt}. shallow depth of field, vignette, highly detailed, high budget Hollywood movie, bokeh, cinemascope, moody",
        "neg_prompt": "anime, cartoon, graphic, text, painting, crayon, graphite, abstract, glitch, deformed, mutated, ugly, disfigured"
    },


        "Synthwave": {
        "prompt": "vaporwave synthwave style {prompt}. cyberpunk, neon, vibes, stunningly beautiful, crisp, detailed, sleek, ultramodern, high contrast, cinematic composition",
        "neg_prompt": "illustration, painting, crayon, graphite, abstract, glitch, deformed, mutated, ugly, disfigured"
    },

        "Isometric": {
        "prompt": "isometric style {prompt}. vibrant, beautiful, crisp, detailed, ultra detailed, intricate",
        "neg_prompt": "deformed, mutated, ugly, disfigured, blur, blurry, noise, noisy, realistic, photographic"
    },

        "Low Poly Game Art": {
        "prompt": "low-poly style {prompt}. ambient occlusion, low-poly game art, polygon mesh, jagged, blocky, wireframe edges, centered composition",
        "neg_prompt": "noisy, sloppy, messy, grainy, highly detailed, ultra textured, photo"
    },


        "Clay Art": {
        "prompt": ", claymation style {prompt}. sculpture, clay art, centered composition, play-doh",
        "neg_prompt": "sloppy, messy, grainy, highly detailed, ultra textured, photo, mutated"
    },

        "3D Model": {
        "prompt": "professional 3d model {prompt} . octane render, highly detailed, volumetric, dramatic lighting",
        "neg_prompt": "ugly, deformed, noisy, low poly, blurry, painting"
    },


        "Origami": {
        "prompt": "origami style {prompt}. paper art, pleated paper, folded, origami art, pleats, cut and fold, centered composition",
        "neg_prompt": "noisy, sloppy, messy, grainy, highly detailed, ultra textured"
    },


        "Line Art": {
        "prompt": "line art drawing {prompt}. professional, sleek, modern, minimalist, graphic, line art, vector graphics",
        "neg_prompt": "anime, photorealistic, 35mm film, deformed, glitch, blurry, noisy, off-center, deformed, cross-eyed, closed eyes, bad anatomy, ugly, disfigured, mutated, realism, realistic, impressionism, expressionism, oil, acrylic"
    },


        "Pixel Art": {
        "prompt": "pixel-art {prompt}. low-res, blocky, pixel art style, 16-bit graphics",
        "neg_prompt": "sloppy, messy, blurry, noisy, highly detailed, ultra textured, photo, realistic"
    },



        "Fabl": {
        "prompt": ", award winning photography, Elke vogelsang",
        "neg_prompt": ""
    }


    }

def style_modifier(input_prompt, input_neg_prompt, style):
  style_prompt= style_dictionary[style]['prompt']
  if "{prompt}" in style_prompt:
    output_prompt = style_prompt.replace("{prompt}", input_prompt)
  else:
    output_prompt= input_prompt + style_dictionary[style]['prompt']

  if input_neg_prompt =='':
    output_neg_prompt=style_dictionary[style]['neg_prompt']
  else:
    output_neg_prompt= input_neg_prompt + ", " + style_dictionary[style]['neg_prompt']

  return output_prompt, output_neg_prompt


output_prompt, output_neg_prompt = style_modifier(input_prompt=input_prompt, input_neg_prompt=input_neg_prompt, style='Origami')

print(output_prompt)
print(output_neg_prompt)
