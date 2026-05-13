#!/bin/bash

echo "🚀 Starting MovieMind Comprehensive Testing Suite"

# Level 1: Backend
echo "------------------------------------------------"
echo "📂 LEVEL 1: Backend Testing (pytest)"
echo "------------------------------------------------"
cd backend
python -m pytest tests/
cd ..

# Level 2: Frontend
echo "------------------------------------------------"
echo "📂 LEVEL 2: Frontend Testing (Jest)"
echo "------------------------------------------------"
cd frontend
npm test -- --watchAll=false
cd ..

# Level 3: E2E
echo "------------------------------------------------"
echo "📂 LEVEL 3: E2E Testing (Playwright)"
echo "------------------------------------------------"
npx playwright test

echo "✅ All tests completed!"
