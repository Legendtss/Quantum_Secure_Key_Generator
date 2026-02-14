#!/bin/bash

# Quantum Key Generator - Start Script
# Starts both backend and frontend in separate terminals

echo "Starting Quantum Key Generator..."
echo ""

# Check if running in tmux or screen
if command -v tmux &> /dev/null; then
    echo "Starting in tmux sessions..."
    
    # Start backend
    tmux new-session -d -s quantum-backend 'cd backend && source venv/bin/activate && python app.py'
    echo "✓ Backend started in tmux session 'quantum-backend'"
    
    # Start frontend
    tmux new-session -d -s quantum-frontend 'cd frontend && npm start'
    echo "✓ Frontend started in tmux session 'quantum-frontend'"
    
    echo ""
    echo "To view backend logs: tmux attach -t quantum-backend"
    echo "To view frontend logs: tmux attach -t quantum-frontend"
    echo "To stop: tmux kill-session -t quantum-backend && tmux kill-session -t quantum-frontend"
else
    echo "Please run the backend and frontend in separate terminals:"
    echo ""
    echo "Terminal 1 (Backend):"
    echo "  cd backend"
    echo "  source venv/bin/activate"
    echo "  python app.py"
    echo ""
    echo "Terminal 2 (Frontend):"
    echo "  cd frontend"
    echo "  npm start"
fi

echo ""
echo "Application will be available at http://localhost:3000"
