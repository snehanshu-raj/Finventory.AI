#!/bin/bash
# dev.sh - Start frontend development server with correct Node version

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Auto-switch to Node version from .nvmrc
if [ -f .nvmrc ]; then
  nvm use
else
  nvm use 20
fi

# Start dev server
npm run dev
