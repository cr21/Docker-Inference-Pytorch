import warnings
warnings.filterwarnings("ignore")
from timm.models import create_model
import hydra
from omegaconf import DictConfig
import time
import requests
from io import BytesIO
import json
import os
import logging
from torch.nn.functional import softmax
from torchvision import transforms
from PIL import Image
from omegaconf import DictConfig, OmegaConf

@hydra.main(config_path="/src/config/",config_name="config")
def main(config:DictConfig)->None:
    # print(OmegaConf.to_yaml(config))
    # print("111"*50)
    labels2classnames=json.load(open('/src/imagenet_1000_class_labels.json','r')) 
    
    model = create_model(model_name=config.model, pretrained=True)

    response=requests.get(config.image)
    img=Image.open(BytesIO(response.content)).convert('RGB')

    transformations = transforms.Compose([
        transforms.Resize((224,224)),
        transforms.ToTensor(),
        transforms.Normalize((0.485, 0.456, 0.406),(0.229, 0.224, 0.225))
    ])
    img = transformations(img).unsqueeze(0)
    output=model(img)
    output=softmax(output,dim=1)
    index=output.argmax().item()

    json_out = {
        'predicted':labels2classnames[str(index)],
        'confidence':output[0, index].item()
    }
    # print("predictions")
    # print("::::"*25)
    print(json.dumps(json_out))



if __name__=='__main__':
    logging.disable(logging.CRITICAL)
    main()
