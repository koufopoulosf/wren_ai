#!/bin/bash
# Setup Sample Database for Wren AI

echo "🚀 Setting up sample database for Wren AI..."
echo ""

# Check if docker-compose is running
if ! docker-compose ps | grep -q "postgres.*Up"; then
    echo "❌ PostgreSQL container is not running"
    echo "   Run: docker-compose up -d postgres"
    exit 1
fi

echo "✅ PostgreSQL container is running"
echo ""

# Load sample data
echo "📊 Loading sample data..."
docker-compose exec -T postgres psql -U wren_user -d analytics < database/setup_sample_data.sql

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Sample data loaded successfully!"
    echo ""
    echo "📋 Sample Schema Created:"
    echo "   - customers (10 rows)"
    echo "   - products (15 rows)"
    echo "   - orders (20 rows)"
    echo "   - order_items (30 rows)"
    echo ""
    echo "🧪 Try these test questions:"
    echo "   - What was total revenue last month?"
    echo "   - Show me top 5 customers by revenue"
    echo "   - Which products are low on stock?"
    echo "   - How many orders from USA customers?"
    echo ""
    echo "🔄 Restart the Streamlit app to load the new schema:"
    echo "   docker-compose restart streamlit-app"
else
    echo "❌ Failed to load sample data"
    exit 1
fi
