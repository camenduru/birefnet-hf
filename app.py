import gradio as gr
from gradio_imageslider import ImageSlider
from loadimg import load_img
import spaces
from transformers import AutoModelForImageSegmentation
import torch
from torchvision import transforms

torch.set_float32_matmul_precision(["high", "highest"][0])

birefnet = AutoModelForImageSegmentation.from_pretrained(
    "ZhengPeng7/BiRefNet", trust_remote_code=True
)
birefnet.to("cuda")
transform_image = transforms.Compose(
    [
        transforms.Resize((1024, 1024)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ]
)


@spaces.GPU
def fn(image):
    im = load_img(image, output_type="pil")
    im = im.convert("RGB")
    image_size = im.size
    origin = im.copy()
    image = load_img(im)
    input_images = transform_image(image).unsqueeze(0).to("cuda")
    # Prediction
    with torch.no_grad():
        preds = birefnet(input_images)[-1].sigmoid().cpu()
    pred = preds[0].squeeze()
    pred_pil = transforms.ToPILImage()(pred)
    mask = pred_pil.resize(image_size)
    image.putalpha(mask)
    return (image, origin)


slider1 = ImageSlider(label="birefnet", type="pil")
slider2 = ImageSlider(label="birefnet", type="pil")
image = gr.Image(label="Upload an image")
text = gr.Textbox(label="Paste an image URL")


chameleon = load_img("chameleon.jpg", output_type="pil")

url = "https://hips.hearstapps.com/hmg-prod/images/gettyimages-1229892983-square.jpg"
tab1 = gr.Interface(
    fn, inputs=image, outputs=slider1, examples=[chameleon], api_name="image"
)

tab2 = gr.Interface(fn, inputs=text, outputs=slider2, examples=[url], api_name="text")


demo = gr.TabbedInterface(
    [tab1, tab2], ["image", "text"], title="birefnet for background removal"
)

if __name__ == "__main__":
    demo.launch()
