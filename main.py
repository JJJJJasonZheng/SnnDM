import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
#from scipy.spatial.distance import pdist
import nltk
from nltk.cluster.kmeans import KMeansClusterer



class SiameseNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        self.cnn1 = nn.Sequential(
            nn.ReflectionPad2d(1),
            nn.Conv2d(1,4,kernel_size=3),
            nn.ReLU(inplace=True),
            nn.BatchNorm2d(4),

            nn.ReflectionPad2d(1),
            nn.Conv2d(4,8,kernel_size=3),
            nn.ReLU(inplace=True),
            nn.BatchNorm2d(8),

            nn.ReflectionPad2d(1),
            nn.Conv2d(8,8,kernel_size=3),
            nn.ReLU(inplace=True),
            nn.BatchNorm2d(8),
        )

        self.fc1 = nn.Sequential(
            nn.Linear(8*64*64,500),
            nn.LeakyReLU(0.5, inplace=True)
            #nn.ReLU(inplace=True),

            #nn.Linear(500,100),
            #nn.ReLU(inplace=True),

            #nn.Linear(100,20)
        )

    def forward_once(self, x):
        output = self.cnn1(x)
        output = output.view(output.size()[0],-1)
        output = self.fc1(output)
        return output

    def forward(self,input1,input2):
        output1 = self.forward_once(input1)
        output2 = self.forward_once(input2)
        return output1, output2  


class ContrastiveLoss(torch.nn.Module):
    def __init__(self,margin=2):
        super(ContrastiveLoss, self).__init__()
        self.margin = margin
  
    def forward(self,output1,output2,label):
        #distance = F.pairwise_distance(output1,output2,keepdim=True)
        distance = 1.0 - torch.cosine_similarity(output1, output2, dim=0)
        loss_constrastive = torch.mean((1-label)*torch.pow(distance,2)+(label)*torch.pow(torch.clamp(self.margin-distance,min=0.0),2))
        return loss_constrastive


#from sklearn.cluster import KMeans
#from sklearn.manifold import TSNE
#from sklearn.decomposition import PCA
#import matplotlib.pyplot as plt
import torch
import torchvision.models as models
import torch.nn as nn
import numpy as np
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def loss_plot(iteration,loss,i):
    plt.figure()
    plt.plot(iteration,loss)
    plt.savefig('loss_gjq' + str(i+1) + '.jpg')
    # plt.show()

def generate_img_txt(root):
    f = open('images_gjq.txt','w')
    for i in range(3):
        #if i == 1:
            for j in range(900):
                if j < 9:
                    img_path = root+'/'+str(i)+'/images00000'+str(j+1)+'.jpg'
                elif j < 99:
                    img_path = root+'/'+str(i)+'/images0000'+str(j+1)+'.jpg'
                else:
                    img_path = root+'/'+str(i)+'/images000'+str(j+1)+'.jpg'
                f.write(img_path+'\n')
        #if i == 1:
        #    for j in range(900):
        #        if j < 9:
        #            img_path = root+'/'+str(i)+'/images00000'+str(j+1)+'.jpg'
        #        elif j < 99:
        #            img_path = root+'/'+str(i)+'/images0000'+str(j+1)+'.jpg'
        #        else:
        #            img_path = root+'/'+str(i)+'/images000'+str(j+1)+'.jpg'
        #        f.write(img_path+'\n')
        #else:
        #for j in range(4500):
        #    if j < 9:
        #        img_path = root+str(i)+'/img00000'+str(j+1)+'_RGB.jpg'
        #    elif j < 99:
        #        img_path = root+str(i)+'/img0000'+str(j+1)+'_RGB.jpg'
        #    elif j < 999:
        #        img_path = root+str(i)+'/img000'+str(j+1)+'_RGB.jpg'
        #    else:
        #        img_path = root+str(i)+'/img00'+str(j+1)+'_RGB.jpg'
        #    f.write(img_path+'\n')
    f.close()

def feature2label(features, dim_reduction='pca'):
    #if dim_reduction == 'tsne':
    #    tsne = TSNE(n_components=2)
    #    X = tsne.fit_transform(features)
    #else:
    #    pca = PCA(n_components=2)
    #    X = pca.fit_transform(features)
    #label = KMeans(16).fit_predict(features)
    kclusterer = KMeansClusterer(3, distance=nltk.cluster.util.cosine_distance, avoid_empty_clusters=True, repeats=15)
    label = kclusterer.cluster(features, assign_clusters=True)
    X = 0
    return X,label

def pretrain(dataloader):
    pre_model = models.resnet18(pretrained=True)
    #print(pre_model)
    #print(pre_model.fc.in_features)
    #pre_model.fc.in_features = pre_model.fc.in_features.to(device)
    pre_model.fc = nn.Linear(pre_model.fc.in_features, 256, bias = False)
    pre_model = pre_model.to(device)
    result = []
    for img in dataloader:
       # pre_model.fc = nn.ReLU()
       # pre_model.eval()
        with torch.no_grad():
            img = img.to(device)
            feature = pre_model(img).data.cpu().numpy().squeeze()
            result.append(feature)
    return result

def cluster_plot(X,labels,i):
    plt.figure()
    for label in np.unique(labels):
        X_labeled = X[labels==label]
        plt.scatter(X_labeled[:,0],X_labeled[:,1])
    plt.savefig('kmeans_gjq'+str(i+1)+'.jpg')
    # plt.show()


import numpy as np
import torch
from torch.utils.data import Dataset
import random
from PIL import Image
import linecache

class SiameseDataset(Dataset):

    def __init__(self, txt, labellist, transform=None):
        self.transform = transform
        self.txt = txt
        self.labellist = labellist
  
    def __getitem__(self, index):
        idx0 = random.randint(0,self.__len__()-1)
        label0 = self.labellist[idx0]
        line0 = linecache.getline(self.txt, idx0+1).strip('\n')
        img0 = Image.open(line0)

        should_get_same_class = random.randint(0,1)
        if should_get_same_class:
            while True:
                idx1 = random.randint(1,self.__len__())
                if self.labellist[idx1-1] == label0:
                    break
        else:
            idx1 = random.randint(1,self.__len__())
        label1 = self.labellist[idx1-1]
        line1 = linecache.getline(self.txt, idx1).strip('\n')
        img1 = Image.open(line1)
        img0 = img0.convert("L")
        img1 = img1.convert("L")

        if self.transform is not None:
            img0 = self.transform(img0)
            img1 = self.transform(img1)
        return img0, img1, torch.from_numpy(np.array([int(label0!=label1)],dtype=np.float32))

    def __len__(self):
        with open(self.txt, 'r') as f:
            num = len(f.readlines())
        return num

class Eval_Dataset(Dataset):

    def __init__(self, txt, transform=None, initial=False):
        self.transform = transform
        self.txt = txt
        self.initial = initial

    def __getitem__(self, index):
        line = linecache.getline(self.txt, index+1).strip('\n')
        img = Image.open(line)

        if not self.initial:
            img = img.convert("L")

        if self.transform is not None:
            img = self.transform(img)
        
        return img

    def __len__(self):
        with open(self.txt, 'r') as f:
            num = len(f.readlines())
        return num  
        
import torch
from torch import optim
import torchvision.transforms as transforms
from torch.utils.data import DataLoader
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
BATCH_SIZE = 64
NUM_EPOCHS = 200

def pre_work():
    init_dataset = Eval_Dataset('images_gjq.txt',transforms.ToTensor(),initial=True)
    init_dataloader = DataLoader(init_dataset)

    init_feature = pretrain(init_dataloader)
    init_labellist = feature2label(init_feature)
    return init_labellist[1]

def train(labellist,batch_size,train_number_epochs,learning_rate):

    train_dataset = SiameseDataset('images_gjq.txt',labellist,transforms.ToTensor())
    train_dataloader = DataLoader(train_dataset,batch_size=batch_size,shuffle=True)


    net = SiameseNetwork().to(device) 
    criterion = ContrastiveLoss()
    optimizer = optim.Adam(net.parameters(),lr=learning_rate)

    counter = []
    loss_history = []
    #iteration_number = 0


    for epoch in range(0,train_number_epochs):
        total_loss = 0
        for i,data in enumerate(train_dataloader):
            img0,img1,label = data
            img0,img1,label = img0.to(device),img1.to(device),label.to(device)

            optimizer.zero_grad()
            output1,output2 = net(img0,img1)
            loss_contrastive = criterion(output1,output2,label)
            loss_contrastive.backward()
            total_loss += loss_contrastive.item()
        
        #loss_contrastive.backward()
        #total_loss += loss_contrastive.item()
        optimizer.step()
        counter.append(epoch)
        loss_history.append(loss_contrastive.item())
        print("Epoch number: {} , Current loss: {:.4f}".format(epoch+1,total_loss/(i+1)))

    torch.save(net.state_dict(),"param0406_gjq_cosineDis.pth")
    return counter, loss_history


def eval():
    eval_dataset = Eval_Dataset('images_gjq.txt',transforms.ToTensor())
    eval_dataloader = DataLoader(eval_dataset)

    net = SiameseNetwork().to(device)
    net.load_state_dict(torch.load("param0406_gjq_cosineDis.pth"))
    features = []

    for img in eval_dataloader:
        #print(img)
        with torch.no_grad():
            img = img.to(device)
            #print(type(img))
            output = net.forward_once(img).data.cpu().numpy().squeeze()
            features.append(output)
    
    X ,new_labellist = feature2label(features)
    return X, new_labellist


if __name__ == '__main__':
    print("----------------------Preparing-----------------------")
    generate_img_txt(root='./5gjq_snr_0_1_2_new')
    init_labellist = pre_work()
    #X, new_labellist = eval()
    for i in range(7):
        print("Round: %d" % (i+1))
        if i==0:
            labellist = init_labellist
        else:
            labellist = new_labellist
        print("----------------------Training-----------------------")
        counter, loss_history = train(labellist,BATCH_SIZE,NUM_EPOCHS,0.0005)
        #loss_plot(counter, loss_history, i)
        print("----------------------Clustering-----------------------")
        X, new_labellist = eval()

        new_labellist_np = np.array(new_labellist)
        name = './gjq_0406/gjq_epoch_' + str(i+1) + '.npy'
        np.save(name, new_labellist_np)
        #cluster_plot(X, new_labellist, i)


