import pickle
import numpy as np
import sys
import io
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from mapping import COMPLETE_MAPPING
import warnings
warnings.filterwarnings('ignore')

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("="*60)
print("ASL FINGERSPELLING CLASSIFIER TRAINING")
print("="*60)

# Use the complete mapping from mapping.py
labels_map = {str(k): v for k, v in COMPLETE_MAPPING.items()}

# Load data
try:
    with open('./data.pickle', 'rb') as f:
        data_dict = pickle.load(f)
except FileNotFoundError:
    print("🛑 ERROR: data.pickle not found!")
    print("Please run 'create_dataset.py' first to process the images.")
    exit()

data = np.asarray(data_dict['data'])
labels = np.asarray(data_dict['labels'])

print(f"\n📊 Dataset Info:")
print(f"   Total samples: {len(data)}")
print(f"   Feature dimensions: {data.shape[1]}")
print(f"   Number of classes: {len(np.unique(labels))}")
print(f"   Classes: {sorted([labels_map.get(str(l), str(l)) for l in np.unique(labels)])}")

# Check for empty or invalid data
if len(data) == 0:
    print("🛑 ERROR: No data found in data.pickle!")
    exit()

# Check data consistency
if len(data) != len(labels):
    print(f"🛑 ERROR: Data and labels mismatch! Data: {len(data)}, Labels: {len(labels)}")
    exit()

# Split data
x_train, x_test, y_train, y_test = train_test_split(
    data, labels, 
    test_size=0.2, 
    shuffle=True, 
    stratify=labels,
    random_state=42
)

print(f"\n📦 Data Split:")
print(f"   Training samples: {len(x_train)}")
print(f"   Test samples: {len(x_test)}")

# Feature Scaling - CRITICAL for better accuracy
print("\n🔧 Applying feature scaling...")
scaler = StandardScaler()
x_train_scaled = scaler.fit_transform(x_train)
x_test_scaled = scaler.transform(x_test)

# Try multiple models and find the best one
print("\n🤖 Training and evaluating models...")
print("-" * 60)

models = {
    'RandomForest (Default)': RandomForestClassifier(random_state=42, n_jobs=-1),
    'RandomForest (Optimized)': RandomForestClassifier(
        n_estimators=200,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    ),
    'SVM (RBF Kernel)': SVC(kernel='rbf', C=10, gamma='scale', random_state=42, probability=True),
}

results = {}
best_model = None
best_score = 0
best_name = ""

for name, model in models.items():
    print(f"\n{'='*60}")
    print(f"Training: {name}")
    print(f"{'='*60}")
    
    # Train on scaled data
    model.fit(x_train_scaled, y_train)
    
    # Predictions
    y_train_pred = model.predict(x_train_scaled)
    y_test_pred = model.predict(x_test_scaled)
    
    # Calculate scores
    train_score = accuracy_score(y_train, y_train_pred)
    test_score = accuracy_score(y_test, y_test_pred)
    
    results[name] = {
        'model': model,
        'train_score': train_score,
        'test_score': test_score
    }
    
    print(f"\n📈 Performance Metrics:")
    print(f"   Training Accuracy: {train_score * 100:.2f}%")
    print(f"   Test Accuracy: {test_score * 100:.2f}%")
    
    # Track best model
    if test_score > best_score:
        best_score = test_score
        best_model = model
        best_name = name

# Display final results
print("\n" + "="*60)
print("TRAINING RESULTS SUMMARY")
print("="*60)

for name, result in results.items():
    print(f"\n{name}:")
    print(f"   Train: {result['train_score']*100:.2f}%")
    print(f"   Test:  {result['test_score']*100:.2f}%")

print("\n" + "="*60)
print(f"🏆 BEST MODEL: {best_name}")
print(f"   Test Accuracy: {best_score * 100:.2f}%")
print("="*60)

# Save the best model along with the scaler
print("\n💾 Saving model and scaler...")
with open('model.p', 'wb') as f:
    pickle.dump({
        'model': best_model,
        'scaler': scaler,
        'labels_map': labels_map
    }, f)

print("✅ Saved 'model.p' successfully!")

# Detailed classification report
print("\n" + "="*60)
print("DETAILED CLASSIFICATION REPORT")
print("="*60)
y_pred = best_model.predict(x_test_scaled)
print("\n" + classification_report(y_test, y_pred, 
                                   target_names=[labels_map.get(str(l), str(l)) for l in sorted(np.unique(labels))]))

print("\nNext step: Run 'inference_classifier.py' for real-time sign language recognition!")
