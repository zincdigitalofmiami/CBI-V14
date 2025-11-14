#!/bin/bash

# CBI-V14 New Machine Setup Script
# This script sets up a brand new Mac for CBI-V14 development
# Moves repositories to external drive for training data optimization

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

EXTERNAL_DRIVE="/Volumes/Satechi Hub"
EXTERNAL_PROJECTS="${EXTERNAL_DRIVE}/Projects"
EXTERNAL_REPO="${EXTERNAL_PROJECTS}/CBI-V14"
EXTERNAL_TRAINING_DATA="${EXTERNAL_REPO}/TrainingData"
EXTERNAL_MODELS="${EXTERNAL_REPO}/Models"
EXTERNAL_LOGS="${EXTERNAL_REPO}/Logs"

echo -e "${GREEN}🚀 CBI-V14 New Machine Setup${NC}"
echo "=============================================="
echo ""

# Check if external drive is mounted
if [ ! -d "$EXTERNAL_DRIVE" ]; then
    echo -e "${RED}❌ External drive not found at: $EXTERNAL_DRIVE${NC}"
    echo "Please ensure 'Satechi Hub' is mounted and try again"
    exit 1
fi

echo -e "${BLUE}STEP 1: Checking Prerequisites...${NC}"

# Check Homebrew
if ! command -v brew &> /dev/null; then
    echo -e "${YELLOW}Installing Homebrew...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
else
    echo "  ✅ Homebrew installed"
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Python3 not found - installing...${NC}"
    brew install python@3.12
else
    echo "  ✅ Python3 installed: $(python3 --version)"
fi

# Check Google Cloud SDK
if ! command -v gcloud &> /dev/null; then
    echo -e "${YELLOW}Installing Google Cloud SDK...${NC}"
    brew install --cask google-cloud-sdk
    echo "  ⚠️  You'll need to restart terminal or run: source ~/.zshrc"
else
    echo "  ✅ Google Cloud SDK installed"
fi

# Check pyenv
if ! command -v pyenv &> /dev/null; then
    echo -e "${YELLOW}Installing pyenv...${NC}"
    brew install pyenv
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
    echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
    echo 'eval "$(pyenv init -)"' >> ~/.zshrc
    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
    echo "  ✅ pyenv installed"
else
    echo "  ✅ pyenv installed"
    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
fi

echo ""
echo -e "${BLUE}STEP 2: Setting up External Drive Structure...${NC}"

# Request Full Disk Access (user needs to grant manually)
echo -e "${YELLOW}⚠️  IMPORTANT: You may need to grant Full Disk Access${NC}"
echo "   System Settings > Privacy & Security > Full Disk Access"
echo "   Add Terminal (or Cursor) to the list"
echo ""

# Try to create directories (may fail without permissions)
if mkdir -p "$EXTERNAL_PROJECTS" 2>/dev/null; then
    echo "  ✅ Created: $EXTERNAL_PROJECTS"
else
    echo -e "${RED}  ❌ Cannot create directories on external drive${NC}"
    echo "  Please grant Full Disk Access and run this script again"
    echo "  Or create manually: mkdir -p \"$EXTERNAL_PROJECTS\""
    exit 1
fi

# Create master directory structure
echo "  📁 Creating master directory structure..."
mkdir -p "${EXTERNAL_REPO}/TrainingData/raw" || echo "  ⚠️  Could not create TrainingData/raw"
mkdir -p "${EXTERNAL_REPO}/TrainingData/processed" || echo "  ⚠️  Could not create TrainingData/processed"
mkdir -p "${EXTERNAL_REPO}/TrainingData/exports" || echo "  ⚠️  Could not create TrainingData/exports"
mkdir -p "${EXTERNAL_REPO}/Models/local" || echo "  ⚠️  Could not create Models/local"
mkdir -p "${EXTERNAL_REPO}/Models/vertex-ai" || echo "  ⚠️  Could not create Models/vertex-ai"
mkdir -p "${EXTERNAL_REPO}/Models/bqml" || echo "  ⚠️  Could not create Models/bqml"
mkdir -p "${EXTERNAL_REPO}/Logs/training" || echo "  ⚠️  Could not create Logs/training"
mkdir -p "${EXTERNAL_REPO}/Logs/ingestion" || echo "  ⚠️  Could not create Logs/ingestion"
mkdir -p "${EXTERNAL_REPO}/Logs/deployment" || echo "  ⚠️  Could not create Logs/deployment"
mkdir -p "${EXTERNAL_DRIVE}/MacData/Desktop" || echo "  ⚠️  Could not create MacData/Desktop"
mkdir -p "${EXTERNAL_DRIVE}/MacData/Downloads" || echo "  ⚠️  Could not create MacData/Downloads"
mkdir -p "${EXTERNAL_DRIVE}/MacData/Documents" || echo "  ⚠️  Could not create MacData/Documents"
mkdir -p "${EXTERNAL_DRIVE}/MacData/Pictures" || echo "  ⚠️  Could not create MacData/Pictures"
mkdir -p "${EXTERNAL_DRIVE}/MacData/Music" || echo "  ⚠️  Could not create MacData/Music"
mkdir -p "${EXTERNAL_DRIVE}/MacData/Movies" || echo "  ⚠️  Could not create MacData/Movies"
mkdir -p "${EXTERNAL_DRIVE}/System/Backups" || echo "  ⚠️  Could not create System/Backups"
mkdir -p "${EXTERNAL_DRIVE}/System/ApplicationSupport" || echo "  ⚠️  Could not create System/ApplicationSupport"
mkdir -p "${EXTERNAL_DRIVE}/System/Cache" || echo "  ⚠️  Could not create System/Cache"
echo "  ✅ Master directory structure created"

echo ""
echo -e "${BLUE}STEP 3: Consolidating Existing Directories...${NC}"

CURRENT_REPO="$HOME/Documents/GitHub/CBI-V14"

# Consolidate existing directories if they exist
if [ -d "$CURRENT_REPO" ]; then
    cd "$CURRENT_REPO"
    
    # Move models directories
    if [ -d "models" ] || [ -d "models_organized" ]; then
        echo "  📦 Consolidating models directories..."
        if [ -d "models" ]; then
            cp -R models/* "${EXTERNAL_MODELS}/local/" 2>/dev/null || echo "  ⚠️  Could not copy models/"
        fi
        if [ -d "models_organized" ]; then
            cp -R models_organized/* "${EXTERNAL_MODELS}/local/" 2>/dev/null || echo "  ⚠️  Could not copy models_organized/"
        fi
        echo "  ✅ Models consolidated to ${EXTERNAL_MODELS}/local/"
    fi
    
    # Move logs directory
    if [ -d "logs" ]; then
        echo "  📦 Consolidating logs directory..."
        cp -R logs/* "${EXTERNAL_LOGS}/training/" 2>/dev/null || echo "  ⚠️  Could not copy logs/"
        echo "  ✅ Logs consolidated to ${EXTERNAL_LOGS}/training/"
    fi
    
    # Move data directory
    if [ -d "data" ]; then
        echo "  📦 Consolidating data directory..."
        cp -R data/* "${EXTERNAL_TRAINING_DATA}/raw/" 2>/dev/null || echo "  ⚠️  Could not copy data/"
        echo "  ✅ Data consolidated to ${EXTERNAL_TRAINING_DATA}/raw/"
    fi
fi

echo ""
echo -e "${BLUE}STEP 4: Moving Git Repositories to External Drive...${NC}"

if [ -d "$CURRENT_REPO" ]; then
    if [ -d "$EXTERNAL_REPO" ] && [ -d "$EXTERNAL_REPO/.git" ]; then
        echo -e "${YELLOW}  ⚠️  Repository already exists on external drive${NC}"
        echo "  Checking if it's up to date..."
        cd "$EXTERNAL_REPO"
        git fetch origin
        git pull origin main || true
    elif [ -d "$EXTERNAL_REPO" ]; then
        echo -e "${YELLOW}  ⚠️  External directory exists but is not a git repo${NC}"
        echo "  Removing and copying fresh..."
        rm -rf "$EXTERNAL_REPO"
        echo "  📦 Moving CBI-V14 to external drive..."
        cp -R "$CURRENT_REPO" "$EXTERNAL_REPO"
        
        cd "$EXTERNAL_REPO"
        if git status &> /dev/null; then
            echo "  ✅ Repository moved successfully"
            
            if [ ! -L "$CURRENT_REPO" ]; then
                echo "  🔗 Creating symlink from original location..."
                mv "$CURRENT_REPO" "${CURRENT_REPO}.backup.$(date +%Y%m%d_%H%M%S)"
                ln -s "$EXTERNAL_REPO" "$CURRENT_REPO"
                echo "  ✅ Symlink created"
            fi
        else
            echo -e "${RED}  ❌ Git repository corrupted during move${NC}"
            exit 1
        fi
    else
        echo "  📦 Moving CBI-V14 to external drive..."
        # Copy repository
        cp -R "$CURRENT_REPO" "$EXTERNAL_REPO"
        
        # Verify git is intact
        cd "$EXTERNAL_REPO"
        if git status &> /dev/null; then
            echo "  ✅ Repository moved successfully"
            
            # Create symlink from original location
            if [ ! -L "$CURRENT_REPO" ]; then
                echo "  🔗 Creating symlink from original location..."
                mv "$CURRENT_REPO" "${CURRENT_REPO}.backup.$(date +%Y%m%d_%H%M%S)"
                ln -s "$EXTERNAL_REPO" "$CURRENT_REPO"
                echo "  ✅ Symlink created"
            fi
        else
            echo -e "${RED}  ❌ Git repository corrupted during move${NC}"
            exit 1
        fi
    fi
else
    echo -e "${YELLOW}  ⚠️  CBI-V14 not found at $CURRENT_REPO${NC}"
    echo "  Will clone fresh to external drive..."
    
    if [ ! -d "$EXTERNAL_REPO" ]; then
        cd "$EXTERNAL_PROJECTS"
        git clone https://github.com/zincdigitalofmiami/CBI-V14.git
        echo "  ✅ Repository cloned to external drive"
    fi
fi

echo ""
echo -e "${BLUE}STEP 5: Installing Python Environments...${NC}"

# Install Python versions
if ! pyenv versions | grep -q "3.10.12"; then
    echo "  📦 Installing Python 3.10.12..."
    pyenv install 3.10.12 || echo "  ⚠️  Python 3.10.12 installation may have issues"
fi

if ! pyenv versions | grep -q "3.12.6"; then
    echo "  📦 Installing Python 3.12.6..."
    pyenv install 3.12.6 || echo "  ⚠️  Python 3.12.6 installation may have issues"
fi

# Set default Python
pyenv global 3.12.6
echo "  ✅ Python 3.12.6 set as default"

# Create virtualenv for TensorFlow Metal
if ! pyenv versions | grep -q "vertex-metal-312"; then
    echo "  📦 Creating vertex-metal-312 virtualenv..."
    pyenv virtualenv 3.12.6 vertex-metal-312 || echo "  ⚠️  Virtualenv may already exist"
fi

echo ""
echo -e "${BLUE}STEP 6: Installing ML Optimization Tools...${NC}"

# Install performance monitoring tools
if ! command -v htop &> /dev/null; then
    echo "  📦 Installing htop (system monitoring)..."
    brew install htop
else
    echo "  ✅ htop installed"
fi

if ! command -v bpytop &> /dev/null; then
    echo "  📦 Installing bpytop (advanced monitoring)..."
    pip3 install bpytop || echo "  ⚠️  bpytop installation may have issues"
else
    echo "  ✅ bpytop installed"
fi

echo ""
echo -e "${BLUE}STEP 7: Installing Project Dependencies...${NC}"

if [ -d "$EXTERNAL_REPO" ]; then
    cd "$EXTERNAL_REPO"

    if command -v pyenv >/dev/null 2>&1; then
        pyenv activate vertex-metal-312 >/dev/null 2>&1 || export PYENV_VERSION=vertex-metal-312
    fi
    
    # Install base requirements
    if [ -f "scripts/requirements.txt" ]; then
        echo "  📦 Installing scripts requirements..."
        pip3 install --upgrade pip
        pip3 install -r scripts/requirements.txt || echo "  ⚠️  Some packages may have failed"
    fi

    if [ -f "src/ingestion/requirements.txt" ]; then
        echo "  📦 Installing ingestion requirements..."
        pip3 install -r src/ingestion/requirements.txt || echo "  ⚠️  Some packages may have failed"
    fi

    if [ -f "docs/forecast/requirements.txt" ]; then
        echo "  📦 Installing forecast requirements..."
        pip3 install -r docs/forecast/requirements.txt || echo "  ⚠️  Some packages may have failed"
    fi
    
    # Install MLX (Apple's native ML framework - OPTIMAL for M4 Mac Mini)
    # MLX is 2-3x faster than TensorFlow Metal for parallel processing
    # Perfect for highly complex data with 100 years of history
    if [[ $(uname -m) == "arm64" ]]; then
        echo "  📦 Installing MLX (Apple Silicon optimized - RECOMMENDED for new training)..."
        pip3 install mlx mlx-lm || echo "  ⚠️  MLX installation may have issues"
        echo "  ✅ MLX installed - optimal for parallel processing on M4 Mac Mini"
    fi
    
    # Install TensorFlow Metal for Apple Silicon (keep as backup/comparison)
    if [[ $(uname -m) == "arm64" ]]; then
        echo "  📦 Installing TensorFlow Metal (backup framework)..."
        pyenv activate vertex-metal-312 || export PYENV_VERSION=vertex-metal-312
        pip3 install tensorflow-macos==2.16.2 tensorflow-metal==1.2.0 keras || echo "  ⚠️  TensorFlow Metal installation may have issues"
        pyenv deactivate >/dev/null 2>&1 || unset PYENV_VERSION
        pyenv global 3.12.6
        echo "  ✅ TensorFlow Metal installed (for comparison/testing)"
    fi
    
    # Install ML optimization packages (for faster data processing)
    echo "  📦 Installing Polars (faster pandas alternative)..."
    pip3 install polars || echo "  ⚠️  Polars installation may have issues"
    
    echo "  📦 Installing DuckDB (for large dataset analysis on external drive)..."
    pip3 install duckdb || echo "  ⚠️  DuckDB installation may have issues"
    
    echo "  📦 Installing DVC (data version control for large datasets)..."
    pip3 install dvc dvc-gdrive || echo "  ⚠️  DVC installation may have issues"
    
    echo "  📦 Installing MLflow (experiment tracking)..."
    pip3 install mlflow || echo "  ⚠️  MLflow installation may have issues"
    
    # Install core data science packages with Apple Silicon optimizations
    echo "  📦 Installing optimized NumPy/Pandas (Apple Silicon)..."
    pip3 install --upgrade numpy pandas scikit-learn || echo "  ⚠️  Some packages may have failed"
    
    echo ""
    echo -e "${BLUE}STEP 7.1: Installing Deep Learning Frameworks...${NC}"
    
    # Install PyTorch (alternative deep learning framework)
    if [[ $(uname -m) == "arm64" ]]; then
        echo "  📦 Installing PyTorch (Apple Silicon optimized)..."
        pip3 install torch torchvision torchaudio || echo "  ⚠️  PyTorch installation may have issues"
    fi
    
    # Install JAX (Google's high-performance ML framework)
    if [[ $(uname -m) == "arm64" ]]; then
        echo "  📦 Installing JAX + jax-metal (Apple Silicon)..."
        pip3 install jax jax-metal || echo "  ⚠️  JAX installation may have issues"
    fi
    
    echo "  📦 Installing Keras 3.0+ (high-level neural network API)..."
    pip3 install keras || echo "  ⚠️  Keras installation may have issues"
    
    echo "  📦 Installing Keras Tuner (hyperparameter optimization)..."
    pip3 install keras-tuner || echo "  ⚠️  Keras Tuner installation may have issues"
    
    echo ""
    echo -e "${BLUE}STEP 7.2: Installing GS Quant / JPM Style Financial Analysis...${NC}"
    
    echo "  📦 Installing quantlib (quantitative finance library)..."
    pip3 install quantlib || echo "  ⚠️  quantlib installation may have issues"
    
    echo "  📦 Installing zipline-reloaded (backtesting engine)..."
    pip3 install zipline-reloaded || echo "  ⚠️  zipline-reloaded installation may have issues"
    
    echo "  📦 Installing backtrader (backtesting framework)..."
    pip3 install backtrader || echo "  ⚠️  backtrader installation may have issues"
    
    echo "  📦 Installing quantstats (portfolio analytics)..."
    pip3 install quantstats || echo "  ⚠️  quantstats installation may have issues"
    
    echo "  📦 Installing pyfolio (portfolio performance analysis)..."
    pip3 install pyfolio-reloaded || echo "  ⚠️  pyfolio installation may have issues"
    
    echo "  📦 Installing empyrical (financial performance metrics)..."
    pip3 install empyrical || echo "  ⚠️  empyrical installation may have issues"
    
    echo ""
    echo -e "${BLUE}STEP 7.3: Installing Advanced Analytics & Statistics...${NC}"
    
    echo "  📦 Installing scipy (scientific computing, statistical functions)..."
    pip3 install scipy || echo "  ⚠️  scipy installation may have issues"
    
    echo "  📦 Installing statsmodels (statistical modeling, time series analysis)..."
    pip3 install statsmodels || echo "  ⚠️  statsmodels installation may have issues"
    
    echo "  📦 Installing arch (ARCH/GARCH models for volatility)..."
    pip3 install arch || echo "  ⚠️  arch installation may have issues"
    
    echo "  📦 Installing pmdarima (ARIMA models)..."
    pip3 install pmdarima || echo "  ⚠️  pmdarima installation may have issues"
    
    echo "  📦 Installing xgboost, lightgbm (gradient boosting)..."
    pip3 install xgboost lightgbm || echo "  ⚠️  gradient boosting installation may have issues"
    
    echo ""
    echo -e "${BLUE}STEP 7.4: Installing Explainability & Interpretability...${NC}"
    
    echo "  📦 Installing SHAP (SHapley Additive exPlanations)..."
    pip3 install shap || echo "  ⚠️  SHAP installation may have issues"
    
    echo "  📦 Installing lime (Local Interpretable Model-agnostic Explanations)..."
    pip3 install lime || echo "  ⚠️  lime installation may have issues"
    
    echo "  📦 Installing eli5 (explain ML models)..."
    pip3 install eli5 || echo "  ⚠️  eli5 installation may have issues"
    
    echo "  📦 Installing interpret (Microsoft's interpretability toolkit)..."
    pip3 install interpret || echo "  ⚠️  interpret installation may have issues"
    
    echo ""
    echo -e "${BLUE}STEP 7.5: Installing Monte Carlo & Simulation...${NC}"
    
    echo "  📦 Installing chaospy (uncertainty quantification)..."
    pip3 install chaospy || echo "  ⚠️  chaospy installation may have issues"
    
    echo ""
    echo -e "${BLUE}STEP 7.6: Installing Financial Metrics & Analysis...${NC}"
    
    echo "  📦 Installing ta-lib (technical analysis library)..."
    # Note: ta-lib requires system library, may need: brew install ta-lib
    pip3 install ta-lib || echo "  ⚠️  ta-lib installation may have issues (may need: brew install ta-lib)"
    
    echo ""
    echo -e "${BLUE}STEP 7.7: Installing Data Processing & Storage...${NC}"
    
    echo "  📦 Installing pyarrow (Parquet file support)..."
    pip3 install pyarrow || echo "  ⚠️  pyarrow installation may have issues"
    
    echo "  📦 Installing h5py (HDF5 file support)..."
    pip3 install h5py || echo "  ⚠️  h5py installation may have issues"
    
    echo ""
    echo -e "${BLUE}STEP 7.8: Installing Experiment Tracking & MLOps...${NC}"
    
    echo "  📦 Installing Weights & Biases (wandb) - alternative experiment tracking..."
    pip3 install wandb || echo "  ⚠️  wandb installation may have issues"
    
    echo "  📦 Installing tensorboard (TensorFlow visualization)..."
    pip3 install tensorboard || echo "  ⚠️  tensorboard installation may have issues"
    
    echo ""
    echo -e "${BLUE}STEP 7.9: Installing Dashboard & Visualization (Python Backend)...${NC}"
    
    echo "  📦 Installing plotly (interactive dashboards, GS/JPM style)..."
    pip3 install plotly plotly-express || echo "  ⚠️  plotly installation may have issues"
    
    echo "  📦 Installing kaleido (Plotly static image export for API endpoints)..."
    pip3 install kaleido || echo "  ⚠️  kaleido installation may have issues"
    
    echo "  📦 Installing matplotlib (static plotting, generate PNG/SVG for API)..."
    pip3 install matplotlib || echo "  ⚠️  matplotlib installation may have issues"
    
    echo "  📦 Installing seaborn (statistical visualizations, generate static images)..."
    pip3 install seaborn || echo "  ⚠️  seaborn installation may have issues"
    
    echo "  📦 Installing bokeh (interactive visualizations, export to static HTML)..."
    pip3 install bokeh || echo "  ⚠️  bokeh installation may have issues"
    
    echo ""
    echo -e "${BLUE}STEP 7.10: Installing API & Endpoints...${NC}"
    
    echo "  📦 Installing FastAPI (high-performance API framework)..."
    pip3 install fastapi || echo "  ⚠️  FastAPI installation may have issues"
    
    echo "  📦 Installing uvicorn (ASGI server)..."
    pip3 install uvicorn || echo "  ⚠️  uvicorn installation may have issues"
    
    echo "  📦 Installing flask (alternative web framework)..."
    pip3 install flask || echo "  ⚠️  flask installation may have issues"
    
    echo "  📦 Installing gunicorn (WSGI server)..."
    pip3 install gunicorn || echo "  ⚠️  gunicorn installation may have issues"
    
    echo ""
    echo -e "${BLUE}STEP 7.11: Installing Google Cloud Packages...${NC}"
    
    echo "  📦 Installing google-cloud-bigquery..."
    pip3 install google-cloud-bigquery || echo "  ⚠️  BigQuery installation may have issues"
    
    echo "  📦 Installing google-cloud-aiplatform (Vertex AI SDK)..."
    pip3 install google-cloud-aiplatform || echo "  ⚠️  Vertex AI installation may have issues"
    
    echo "  📦 Installing google-cloud-storage..."
    pip3 install google-cloud-storage || echo "  ⚠️  Cloud Storage installation may have issues"
    
    echo "  📦 Installing google-cloud-secret-manager..."
    pip3 install google-cloud-secret-manager || echo "  ⚠️  Secret Manager installation may have issues"
    
    echo ""
    echo -e "${BLUE}STEP 7.12: Installing Utilities...${NC}"
    
    echo "  📦 Installing pyyaml (configuration files)..."
    pip3 install pyyaml || echo "  ⚠️  pyyaml installation may have issues"
    
    echo "  📦 Installing click (CLI interfaces)..."
    pip3 install click || echo "  ⚠️  click installation may have issues"
    
    echo "  📦 Installing python-dotenv (environment variables)..."
    pip3 install python-dotenv || echo "  ⚠️  python-dotenv installation may have issues"
    
    echo "  📦 Installing tqdm (progress bars)..."
    pip3 install tqdm || echo "  ⚠️  tqdm installation may have issues"

    if command -v pyenv >/dev/null 2>&1; then
        pyenv deactivate >/dev/null 2>&1 || unset PYENV_VERSION
        pyenv global 3.12.6
    fi
fi

echo ""
echo -e "${BLUE}STEP 8: macOS System Defaults Configuration...${NC}"

echo -e "${YELLOW}⚠️  macOS System Defaults Configuration (Manual Steps Required)${NC}"
echo ""
echo "To configure macOS to save to external drive:"
echo ""
echo "1. Desktop Folder:"
echo "   Right-click Desktop → Get Info → Location → Choose → Select external drive"
echo ""
echo "2. Downloads Folder:"
echo "   Right-click Downloads → Get Info → Location → Choose → Select external drive"
echo ""
echo "3. Documents Folder (non-repo files only):"
echo "   Right-click Documents → Get Info → Location → Choose → Select external drive"
echo "   Note: Keep iCloud Drive connection active for machine core keys"
echo ""
echo "4. Screenshots:"
echo "   Run: defaults write com.apple.screencapture location \"${EXTERNAL_DRIVE}/MacData/Desktop\""
echo "   Then: killall SystemUIServer"
echo ""
echo "5. iCloud Drive:"
echo "   System Settings → Apple ID → iCloud → iCloud Drive"
echo "   Keep enabled for machine core keys"
echo "   For large files, manually move to external drive"
echo ""

echo ""
echo -e "${BLUE}STEP 9: Google Cloud Setup (Manual Required)${NC}"
echo ""
echo -e "${YELLOW}You need to manually authenticate Google Cloud:${NC}"
echo ""
echo "Run these commands:"
echo "  gcloud auth login zinc@zincdigital.co"
echo "  gcloud config set project cbi-v14"
echo "  gcloud config set compute/region us-central1"
echo "  gcloud config set compute/zone us-central1-a"
echo "  gcloud auth application-default login"
echo ""
echo "Then verify with:"
echo "  gcloud config list"
echo "  gcloud auth list"
echo ""

echo ""
echo -e "${BLUE}STEP 10: BigQuery Data Export...${NC}"

echo -e "${YELLOW}⚠️  BigQuery Data Export (Manual/API Required)${NC}"
echo ""
echo "To export training datasets from BigQuery to external drive:"
echo ""
echo "1. Export production_training_data tables:"
echo "   python3 -c \"
from google.cloud import bigquery
import pyarrow.parquet as pq
client = bigquery.Client(project='cbi-v14')
for horizon in ['1w', '1m', '3m', '6m']:
    table_id = f'cbi-v14.models_v4.production_training_data_{horizon}'
    query = f'SELECT * FROM \`{table_id}\`'
    df = client.query(query).to_dataframe()
    output_path = '${EXTERNAL_TRAINING_DATA}/exports/production_training_data_{horizon}.parquet'
    df.to_parquet(output_path, index=False)
    print(f'Exported {horizon}: {len(df)} rows')
\""
echo ""
echo "2. Export historical data (100 years) from forecasting_data_warehouse:"
echo "   This requires custom script based on specific tables needed"
echo "   Save to: ${EXTERNAL_TRAINING_DATA}/raw/"
echo ""

echo ""
echo -e "${BLUE}STEP 11: Setting Environment Variables...${NC}"

# Add to .zshrc
if ! grep -q "CBI_V14_REPO" ~/.zshrc 2>/dev/null; then
    cat >> ~/.zshrc << EOF

# CBI-V14 Configuration
export EXTERNAL_DRIVE="$EXTERNAL_DRIVE"
export CBI_V14_REPO="$EXTERNAL_REPO"
export CBI_V14_TRAINING_DATA="$EXTERNAL_TRAINING_DATA"
export CBI_V14_MODELS="$EXTERNAL_MODELS"
export CBI_V14_LOGS="$EXTERNAL_LOGS"
alias cbi='cd "$EXTERNAL_REPO"'
alias cbdata='cd "$EXTERNAL_TRAINING_DATA"'

# TensorFlow Metal GPU optimization
export TF_METAL_DEVICE_PLACEMENT=1

# Parallel processing optimization
export OMP_NUM_THREADS=$(sysctl -n hw.ncpu)
export POLARS_MAX_THREADS=$(sysctl -n hw.ncpu)
export NUMBA_NUM_THREADS=$(sysctl -n hw.ncpu)
export MKL_NUM_THREADS=$(sysctl -n hw.ncpu)
EOF
    echo "  ✅ Environment variables added to ~/.zshrc"
    echo "  Run: source ~/.zshrc to activate"
else
    echo "  ✅ Environment variables already configured"
fi

echo ""
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "================================"
echo ""
echo "Next Steps:"
echo "1. ✅ Grant Full Disk Access (if not done):"
echo "   System Settings > Privacy & Security > Full Disk Access"
echo "   Add Terminal/Cursor to the list"
echo ""
echo "2. ✅ Authenticate Google Cloud (see commands above)"
echo ""
echo "3. ✅ Reload shell configuration:"
echo "   source ~/.zshrc"
echo ""
echo "4. ✅ Navigate to project:"
echo "   cd \"$EXTERNAL_REPO\""
echo "   or use: cbi"
echo ""
echo "5. ✅ Verify setup:"
echo "   python3 --version"
echo "   gcloud config list"
echo "   git status"
echo ""
echo "6. ✅ Test ML tools:"
echo "   python3 -c 'import mlx.core as mx; print(\"MLX:\", mx.__version__)'"
echo "   python3 -c 'import polars as pl; print(\"Polars:\", pl.__version__)'"
echo "   python3 -c 'import duckdb; print(\"DuckDB:\", duckdb.__version__)'"
echo "   python3 -c 'import tensorflow as tf; print(\"TensorFlow:\", tf.__version__)'"
echo "   python3 -c 'import tensorflow as tf; gpus = tf.config.list_physical_devices(\"GPU\"); print(\"GPU Devices:\", gpus)'"
echo ""
echo "Repository Location: $EXTERNAL_REPO"
echo "Training Data Location: $EXTERNAL_TRAINING_DATA"
echo "Models Location: $EXTERNAL_MODELS"
echo "Logs Location: $EXTERNAL_LOGS"
echo ""
echo -e "${YELLOW}📊 ML Optimization Tools Installed:${NC}"
echo "  ✅ MLX - Apple's native ML framework (PRIMARY for training)"
echo "     • 2-3x faster than TensorFlow Metal for parallel processing"
echo "     • Optimized for M4 Mac Mini with complex data"
echo "     • Automatic parallelization across CPU/GPU/Neural Engine"
echo "  ✅ TensorFlow Metal - Backup framework (for comparison)"
echo "  ✅ Polars - Faster pandas alternative (parallel data processing)"
echo "  ✅ DuckDB - Query large datasets on external drive (parallel SQL)"
echo "  ✅ DVC - Version control for large training datasets"
echo "  ✅ MLflow - Experiment tracking and model registry"
echo "  ✅ htop/bpytop - System monitoring during training"
echo ""
echo -e "${YELLOW}💡 Usage Tips for Parallel Processing:${NC}"
echo "  • START WITH MLX for new training (optimal for M4 Mac Mini)"
echo "  • Use Polars instead of pandas for 2-10x faster parallel data processing"
echo "  • Use DuckDB to query 100 years of data in parallel without loading into memory"
echo "  • MLX automatically uses all CPU/GPU/Neural Engine cores for training"
echo "  • Monitor parallel processing: bpytop (press 'g' for GPU view, 'c' for CPU)"
echo "  • For complex data: MLX > TensorFlow Metal (2-3x speedup)"
echo ""
echo -e "${YELLOW}🚀 Next Steps for Training:${NC}"
echo "  1. Load data with Polars/DuckDB (parallel processing)"
echo "  2. Train models with MLX (automatic parallelization)"
echo "  3. Track experiments with MLflow"
echo "  4. Monitor performance with bpytop"
echo ""


