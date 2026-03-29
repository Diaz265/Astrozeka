import torch

device = "mps" if torch.backends.mps.is_available() else "cpu"

model.train(
    ...
    device=device,  # Will use MPS on your M2
    ...
)