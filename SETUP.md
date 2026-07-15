# Sign Language Detector - Setup Guide

## Virtual Environment Setup

A virtual environment has been created in the `venv` folder. All required packages have been installed.

## How to Run

### 1. Activate the Virtual Environment

**Windows PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows Command Prompt:**
```cmd
venv\Scripts\activate.bat
```

### 2. Run the Project

The project has three main scripts:

#### A. Collect Images (`collect_imgs.py`)
Collects images from your webcam for training:
```bash
python collect_imgs.py
```

#### B. Create Dataset (`create_dataset.py`)
Processes collected images and creates the dataset:
```bash
python create_dataset.py
```

#### C. Train Classifier (`train_classifier.py`)
Trains the machine learning model:
```bash
python train_classifier.py
```

#### D. Run Inference (`inference_classifier.py`)
Runs the sign language detector using your webcam:
```bash
python inference_classifier.py
```

## Requirements

All requirements are installed in the virtual environment:
- opencv-python (>=4.7.0)
- mediapipe (>=0.10.5)
- scikit-learn (>=1.2.0)
- numpy (>=1.21.0)

## Notes

- Make sure you have a webcam connected
- Press 'q' to quit the inference application
- The model file (`model.p`) must exist before running inference (run `train_classifier.py` first)

