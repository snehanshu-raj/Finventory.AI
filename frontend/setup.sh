#!/bin/bash
# Setup script - Run this once to configure your environment

echo "🚀 Setting up Finventory development environment..."
echo ""

# Step 1: Ensure nvm is loaded
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Step 2: Switch to Node 20
echo "📦 Switching to Node.js 20..."
nvm use 20
node_version=$(node --version)
echo "✅ Using Node $node_version"
echo ""

# Step 3: Install dependencies (if not already done)
echo "📚 Installing frontend dependencies..."
cd "$(dirname "$0")"
npm install
echo "✅ Dependencies installed"
echo ""

echo "🎉 Setup complete!"
echo ""
echo "To start development:"
echo "  cd /home/srj/finventory/frontend"
echo "  npm run dev"
echo ""
echo "The frontend will be available at http://localhost:5173"
