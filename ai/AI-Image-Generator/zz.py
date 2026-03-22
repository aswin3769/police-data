import torch

print("CUDA Available:", torch.cuda.is_available())
print("CUDA Version:", torch.version.cuda)

print("cuDNN Available:", torch.backends.cudnn.is_available())
print("cuDNN Version:", torch.backends.cudnn.version())
