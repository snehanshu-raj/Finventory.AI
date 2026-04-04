#!/bin/bash
# Auto-switch Node version when entering frontend directory

# Load nvm if not already loaded
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Check for .nvmrc and switch to that version
if [ -f .nvmrc ]; then
  nvm use
fi
