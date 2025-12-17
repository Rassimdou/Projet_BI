// ============================================================================
// NORTHWIND BI DASHBOARD - JAVASCRIPT
// ============================================================================

// Global variables
let factSales = [];
let dimCustomers = [];
let dimProducts = [];
let dimEmployees = [];
let filteredData = [];

// ============================================================================
// DATA LOADING
// ============================================================================

async function loadCSV(filename) {
    try {
        const response = await fetch(`data/${filename}`);
        const csvText = await response.text();

        return new Promise((resolve, reject) => {
            Papa.parse(csvText, {
                header: true,
                dynamicTyping: true,
                skipEmptyLines: true,
                complete: (results) => resolve(results.data),
                error: (error) => reject(error)
            });
        });
    } catch (error) {
        console.error(`Error loading ${filename}:`, error);
        return [];
    }
}

async function loadAllData() {
    console.log('Loading data from BOTH SQL Server and Access databases...');

    try {
        // Load SQL Server data
        const [sqlFactSales, sqlCustomers, sqlProducts, sqlEmployees] = await Promise.all([
            loadCSV('Fact_Sales.csv'),
            loadCSV('Dim_Customers.csv'),
            loadCSV('Dim_Products.csv'),
            loadCSV('Dim_Employees.csv')
        ]);

        // Load Access data
        const [accessOrders, accessCustomers, accessProducts, accessEmployees, accessOrderDetails] = await Promise.all([
            loadCSV('access_Orders.csv'),
            loadCSV('access_Customers.csv'),
            loadCSV('access_Products.csv'),
            loadCSV('access_Employees.csv'),
            loadCSV('access_Order_Details.csv')
        ]);

        console.log('SQL Server data loaded:', {
            factSales: sqlFactSales.length,
            customers: sqlCustomers.length,
            products: sqlProducts.length,
            employees: sqlEmployees.length
        });

        console.log('Access data loaded:', {
            orders: accessOrders.length,
            customers: accessCustomers.length,
            products: accessProducts.length,
            employees: accessEmployees.length,
            orderDetails: accessOrderDetails.length
        });

        // Check if we actually have Access data
        const hasAccessData = accessOrderDetails.length > 0;

        if (hasAccessData) {
            console.log('✅ Access data available - will merge');
        } else {
            console.log('ℹ️  No Access data - using SQL Server only');
        }

        // Merge customers from both sources
        dimCustomers = [...sqlCustomers];

        // Add Access customers (normalize column names) - only if available
        if (hasAccessData) {
            accessCustomers.forEach(customer => {
                dimCustomers.push({
                    CustomerID: `ACC_${customer.ID}`,
                    CompanyName: customer.Company || 'Unknown',
                    ContactName: `${customer['First Name'] || ''} ${customer['Last Name'] || ''}`.trim() || 'Unknown',
                    Country: customer['Country/Region'] || 'USA',
                    City: customer.City || 'Unknown',
                    Address: customer.Address || '',
                    Phone: customer['Business Phone'] || '',
                    _source: 'Access'
                });
            });
        }

        // Merge products from both sources
        dimProducts = [...sqlProducts];

        // Add Access products (normalize column names)
        accessProducts.forEach(product => {
            dimProducts.push({
                ProductID: `ACC_${product.ID}`,
                ProductName: product['Product Name'] || 'Unknown',
                CategoryName: product.Category || 'General',
                UnitPrice: parseFloat(product['List Price']) || 0,
                _source: 'Access'
            });
        });

        // Merge employees from both sources
        dimEmployees = [...sqlEmployees];

        // Add Access employees (normalize column names)
        accessEmployees.forEach(employee => {
            dimEmployees.push({
                EmployeeID: `ACC_${employee.ID}`,
                FirstName: employee['First Name'] || '',
                LastName: employee['Last Name'] || '',
                _source: 'Access'
            });
        });

        // Start with SQL Server fact sales
        factSales = [...sqlFactSales];

        // Create fact sales from Access order details - only if available
        if (hasAccessData) {
            accessOrderDetails.forEach(detail => {
                const order = accessOrders.find(o => o['Order ID'] === detail['Order ID']);
                if (order) {
                    factSales.push({
                        OrderID: `ACC_${detail['Order ID']}`,
                        OrderDate: order['Order Date'] ? new Date(order['Order Date']) : new Date(),
                        CustomerID: `ACC_${order['Customer ID']}`,
                        EmployeeID: `ACC_${order['Employee ID']}`,
                        ProductID: `ACC_${detail['Product ID']}`,
                        Quantity: parseFloat(detail.Quantity) || 0,
                        UnitPrice: parseFloat(detail['Unit Price']) || 0,
                        Discount: parseFloat(detail.Discount) || 0,
                        TotalAmount: (parseFloat(detail.Quantity) || 0) * (parseFloat(detail['Unit Price']) || 0) * (1 - (parseFloat(detail.Discount) || 0)),
                        _source: 'Access'
                    });
                }
            });

            // Add Access orders that have NO details (empty orders) to ensure Order Count is correct
            // The user expects 878 total orders (830 SQL + 48 Access)
            // Currently missing 9 orders that have no items
            accessOrders.forEach(order => {
                const hasDetails = accessOrderDetails.some(d => d['Order ID'] === order['Order ID']);
                if (!hasDetails) {
                    factSales.push({
                        OrderID: `ACC_${order['Order ID']}`,
                        OrderDate: order['Order Date'] ? new Date(order['Order Date']) : new Date(),
                        CustomerID: `ACC_${order['Customer ID']}`,
                        EmployeeID: `ACC_${order['Employee ID']}`,
                        ProductID: 'UNKNOWN',
                        Quantity: 0,
                        UnitPrice: 0,
                        Discount: 0,
                        TotalAmount: 0,
                        _source: 'Access'
                    });
                }
            });
        }

        // Convert date strings to Date objects for SQL Server data
        factSales.forEach(row => {
            if (row.OrderDate && !(row.OrderDate instanceof Date)) {
                row.OrderDate = new Date(row.OrderDate);
            }
        });

        // Summary
        if (hasAccessData) {
            console.log('✅ DATA MERGED!');
            console.log(`📊 Total Transactions: ${factSales.length}`);
            const uniqueOrders = new Set(factSales.map(r => r.OrderID)).size;
            console.log(`📦 Total Unique Orders: ${uniqueOrders} (Expect ~878)`);
            console.log(`👥 Total Customers: ${dimCustomers.length} (Expect 120)`);
        } else {
            console.log('✅ DATA LOADED (SQL Server only)');
        }

        return true;
    } catch (error) {
        console.error('Error loading data:', error);
        alert('Error loading data files. Please ensure all CSV files are in the data/ folder.');
        return false;
    }
}

// ============================================================================
// DATA MERGING AND FILTERING
// ============================================================================

function mergeData() {
    const merged = factSales.map(sale => {
        const customer = dimCustomers.find(c => c.CustomerID === sale.CustomerID) || {};
        const product = dimProducts.find(p => p.ProductID === sale.ProductID) || {};
        const employee = dimEmployees.find(e => e.EmployeeID === sale.EmployeeID) || {};

        return {
            ...sale,
            CompanyName: customer.CompanyName || 'Unknown',
            Country: customer.Country || 'Unknown',
            ProductName: product.ProductName || 'Unknown',
            CategoryName: product.CategoryName || 'Unknown',
            UnitPrice: product.UnitPrice || sale.UnitPrice || 0,
            EmployeeName: employee.FirstName && employee.LastName
                ? `${employee.FirstName} ${employee.LastName}`
                : 'Unknown'
        };
    });

    return merged;
}

function applyFilters() {
    const startDate = new Date(document.getElementById('startDate').value);
    const endDate = new Date(document.getElementById('endDate').value);

    // Get selected countries
    const allCountriesChecked = document.getElementById('allCountries').checked;
    let selectedCountries = [];

    if (allCountriesChecked) {
        selectedCountries = [...new Set(dimCustomers.map(c => c.Country))];
    } else {
        const countryCheckboxes = document.querySelectorAll('#countryList input[type="checkbox"]:checked');
        selectedCountries = Array.from(countryCheckboxes).map(cb => cb.value);
    }

    // Get selected categories
    const allCategoriesChecked = document.getElementById('allCategories').checked;
    let selectedCategories = [];

    if (allCategoriesChecked) {
        selectedCategories = [...new Set(dimProducts.map(p => p.CategoryName))];
    } else {
        const categoryCheckboxes = document.querySelectorAll('#categoryList input[type="checkbox"]:checked');
        selectedCategories = Array.from(categoryCheckboxes).map(cb => cb.value);
    }

    // Merge and filter data
    const merged = mergeData();

    filteredData = merged.filter(row => {
        const orderDate = row.OrderDate;
        const dateMatch = orderDate >= startDate && orderDate <= endDate;
        const countryMatch = selectedCountries.includes(row.Country);
        const categoryMatch = selectedCategories.includes(row.CategoryName);

        return dateMatch && countryMatch && categoryMatch;
    });

    console.log('Filtered data:', filteredData.length, 'rows');

    updateDashboard();
}

// ============================================================================
// KPI CALCULATIONS
// ============================================================================

function calculateKPIs() {
    const totalRevenue = filteredData.reduce((sum, row) => sum + (row.TotalAmount || 0), 0);
    const uniqueOrders = [...new Set(filteredData.map(row => row.OrderID))];
    const totalOrders = uniqueOrders.length;

    // Calculate average order value
    const orderTotals = {};
    filteredData.forEach(row => {
        if (!orderTotals[row.OrderID]) {
            orderTotals[row.OrderID] = 0;
        }
        orderTotals[row.OrderID] += row.TotalAmount || 0;
    });
    const avgOrderValue = totalOrders > 0 ? totalRevenue / totalOrders : 0;

    // Calculate Total Customers based on Country filter (ignoring Date filter) to show full customer base
    // User requested to see all 120 customers
    let totalCustomers = 0;
    const allCountriesChecked = document.getElementById('allCountries').checked;

    if (allCountriesChecked) {
        totalCustomers = dimCustomers.length;
    } else {
        const countryCheckboxes = document.querySelectorAll('#countryList input[type="checkbox"]:checked');
        const selectedCountries = Array.from(countryCheckboxes).map(cb => cb.value);
        totalCustomers = dimCustomers.filter(c => selectedCountries.includes(c.Country)).length;
    }
    const totalQuantity = filteredData.reduce((sum, row) => sum + (row.Quantity || 0), 0);
    const avgItemsPerOrder = totalOrders > 0 ? totalQuantity / totalOrders : 0;

    // Calculate standard deviation for revenue
    const revenues = Object.values(orderTotals);
    const mean = avgOrderValue;
    const variance = revenues.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / revenues.length;
    const stdDev = Math.sqrt(variance);

    return {
        totalRevenue,
        totalOrders,
        avgOrderValue,
        totalCustomers,
        avgItemsPerOrder,
        totalQuantity,
        stdDev
    };
}

function updateKPIs() {
    const kpis = calculateKPIs();

    document.getElementById('totalRevenue').textContent = `$${kpis.totalRevenue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    document.getElementById('revenueDelta').textContent = `${(kpis.totalRevenue / 100000 * 100).toFixed(1)}% of budget`;

    document.getElementById('totalOrders').textContent = kpis.totalOrders.toLocaleString();
    document.getElementById('ordersDelta').textContent = `Avg: ${(kpis.totalQuantity / Math.max(kpis.totalOrders, 1)).toFixed(0)} units/order`;

    document.getElementById('avgOrderValue').textContent = `$${kpis.avgOrderValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    document.getElementById('avgDelta').textContent = `$${kpis.stdDev.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} std dev`;

    document.getElementById('totalCustomers').textContent = kpis.totalCustomers.toLocaleString();
    document.getElementById('customersDelta').textContent = `$${(kpis.totalRevenue / Math.max(kpis.totalCustomers, 1)).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} per customer`;

    document.getElementById('avgItems').textContent = kpis.avgItemsPerOrder.toFixed(1);
    document.getElementById('itemsDelta').textContent = `Total units: ${kpis.totalQuantity.toLocaleString()}`;

    document.getElementById('filteredRecords').textContent = filteredData.length.toLocaleString();
}

// ============================================================================
// CHART CREATION
// ============================================================================

function createSalesTrendChart() {
    // Group by date
    const dailySales = {};
    filteredData.forEach(row => {
        const date = row.OrderDate.toISOString().split('T')[0];
        if (!dailySales[date]) {
            dailySales[date] = 0;
        }
        dailySales[date] += row.TotalAmount || 0;
    });

    const dates = Object.keys(dailySales).sort();
    const revenues = dates.map(date => dailySales[date]);

    const trace = {
        x: dates,
        y: revenues,
        type: 'scatter',
        mode: 'lines+markers',
        marker: { color: '#2E86AB', size: 6 },
        line: { color: '#2E86AB', width: 2 },
        fill: 'tozeroy',
        fillcolor: 'rgba(46, 134, 171, 0.2)',
        name: 'Revenue'
    };

    const layout = {
        title: '',
        xaxis: { title: 'Order Date', color: '#9aa0a6', gridcolor: '#3a4152' },
        yaxis: { title: 'Revenue ($)', color: '#9aa0a6', gridcolor: '#3a4152' },
        hovermode: 'x unified',
        plot_bgcolor: '#1a1f2e',
        paper_bgcolor: '#242b3d',
        font: { color: '#e8eaed' },
        margin: { l: 60, r: 20, t: 20, b: 60 }
    };

    Plotly.newPlot('salesTrendChart', [trace], layout, { responsive: true });
}

function createCountriesChart() {
    // Group by country
    const countrySales = {};
    filteredData.forEach(row => {
        if (!countrySales[row.Country]) {
            countrySales[row.Country] = 0;
        }
        countrySales[row.Country] += row.TotalAmount || 0;
    });

    // Get top 10
    const sorted = Object.entries(countrySales)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);

    const countries = sorted.map(item => item[0]);
    const revenues = sorted.map(item => item[1]);

    const trace = {
        y: countries,
        x: revenues,
        type: 'bar',
        orientation: 'h',
        marker: {
            color: revenues,
            colorscale: 'Blues',
            showscale: false
        }
    };

    const layout = {
        title: '',
        xaxis: { title: 'Revenue ($)', color: '#9aa0a6', gridcolor: '#3a4152' },
        yaxis: { title: '', color: '#9aa0a6' },
        plot_bgcolor: '#1a1f2e',
        paper_bgcolor: '#242b3d',
        font: { color: '#e8eaed' },
        margin: { l: 120, r: 20, t: 20, b: 60 }
    };

    Plotly.newPlot('countriesChart', [trace], layout, { responsive: true });
}

function createProductsChart() {
    // Group by product
    const productSales = {};
    filteredData.forEach(row => {
        if (!productSales[row.ProductName]) {
            productSales[row.ProductName] = 0;
        }
        productSales[row.ProductName] += row.TotalAmount || 0;
    });

    // Get top 10
    const sorted = Object.entries(productSales)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);

    const products = sorted.map(item => item[0]);
    const revenues = sorted.map(item => item[1]);

    const trace = {
        y: products,
        x: revenues,
        type: 'bar',
        orientation: 'h',
        marker: {
            color: revenues,
            colorscale: 'Oranges',
            showscale: false
        }
    };

    const layout = {
        title: '',
        xaxis: { title: 'Revenue ($)', color: '#9aa0a6', gridcolor: '#3a4152' },
        yaxis: { title: '', color: '#9aa0a6' },
        plot_bgcolor: '#1a1f2e',
        paper_bgcolor: '#242b3d',
        font: { color: '#e8eaed' },
        margin: { l: 180, r: 20, t: 20, b: 60 }
    };

    Plotly.newPlot('productsChart', [trace], layout, { responsive: true });
}

function createCategoryChart() {
    // Group by category
    const categorySales = {};
    filteredData.forEach(row => {
        if (!categorySales[row.CategoryName]) {
            categorySales[row.CategoryName] = 0;
        }
        categorySales[row.CategoryName] += row.TotalAmount || 0;
    });

    const categories = Object.keys(categorySales);
    const revenues = Object.values(categorySales);

    const trace = {
        labels: categories,
        values: revenues,
        type: 'pie',
        hole: 0.6, // Donut chart
        marker: {
            colors: [
                '#6366F1', '#EC4899', '#10B981', '#F59E0B',
                '#8B5CF6', '#06B6D4', '#F43F5E', '#84CC16'
            ]
        },
        textinfo: 'percent',
        textposition: 'outside',
        hovertemplate: '<b>%{label}</b><br>Revenue: $%{value:,.2f}<br>(%{percent})<extra></extra>',
        automargin: true
    };

    const layout = {
        title: '',
        plot_bgcolor: 'rgba(0,0,0,0)',
        paper_bgcolor: 'rgba(0,0,0,0)',
        font: { family: 'Inter, sans-serif', color: '#e2e8f0' },
        margin: { l: 20, r: 20, t: 20, b: 20 },
        showlegend: true,
        legend: {
            orientation: 'v',
            x: 1.1,
            y: 0.5,
            font: { color: '#94a3b8' }
        },
        height: 350
    };

    Plotly.newPlot('categoryChart', [trace], layout, { responsive: true, displayModeBar: false });
}

function createCustomersChart() {
    // Group by customer
    const customerSales = {};
    filteredData.forEach(row => {
        const key = `${row.CustomerID}|${row.CompanyName}`;
        if (!customerSales[key]) {
            customerSales[key] = 0;
        }
        customerSales[key] += row.TotalAmount || 0;
    });

    // Get top 10
    const sorted = Object.entries(customerSales)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);

    const customers = sorted.map(item => item[0].split('|')[1]);
    const revenues = sorted.map(item => item[1]);

    const trace = {
        y: customers,
        x: revenues,
        type: 'bar',
        orientation: 'h',
        marker: {
            color: revenues,
            colorscale: 'Greens',
            showscale: false
        }
    };

    const layout = {
        title: '',
        xaxis: { title: 'Revenue ($)', color: '#9aa0a6', gridcolor: '#3a4152' },
        yaxis: { title: '', color: '#9aa0a6' },
        plot_bgcolor: '#1a1f2e',
        paper_bgcolor: '#242b3d',
        font: { color: '#e8eaed' },
        margin: { l: 180, r: 20, t: 20, b: 60 }
    };

    Plotly.newPlot('customersChart', [trace], layout, { responsive: true });
}

function createMonthlyChart() {
    // Group by month
    const monthlySales = {};
    const monthlyOrders = {};

    filteredData.forEach(row => {
        const month = row.OrderDate.toISOString().substring(0, 7); // YYYY-MM
        if (!monthlySales[month]) {
            monthlySales[month] = 0;
            monthlyOrders[month] = new Set();
        }
        monthlySales[month] += row.TotalAmount || 0;
        monthlyOrders[month].add(row.OrderID);
    });

    const months = Object.keys(monthlySales).sort();
    const revenues = months.map(month => monthlySales[month]);
    const orders = months.map(month => monthlyOrders[month].size);

    const trace1 = {
        x: months,
        y: orders,
        type: 'bar',
        name: 'Orders Count',
        marker: { color: '#A23B72' },
        yaxis: 'y'
    };

    const trace2 = {
        x: months,
        y: revenues,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Revenue',
        line: { color: '#F18F01', width: 3 },
        marker: { size: 8 },
        yaxis: 'y2'
    };

    const layout = {
        title: '',
        xaxis: { title: 'Month', color: '#9aa0a6', gridcolor: '#3a4152' },
        yaxis: {
            title: 'Orders Count',
            color: '#9aa0a6',
            gridcolor: '#3a4152'
        },
        yaxis2: {
            title: 'Revenue ($)',
            overlaying: 'y',
            side: 'right',
            color: '#9aa0a6'
        },
        hovermode: 'x unified',
        plot_bgcolor: '#1a1f2e',
        paper_bgcolor: '#242b3d',
        font: { color: '#e8eaed' },
        margin: { l: 60, r: 60, t: 20, b: 60 },
        showlegend: true,
        legend: { x: 0, y: 1.1, orientation: 'h' }
    };

    Plotly.newPlot('monthlyChart', [trace1, trace2], layout, { responsive: true });
}

// ============================================================================
// 3D CHART CREATION
// ============================================================================

function create3DScatterChart() {
    // Create 3D scatter plot: Country x Category x Time (bubble size = revenue)
    const dataPoints = [];

    // Aggregate data by country, category, and month
    const aggregated = {};
    filteredData.forEach(row => {
        const month = row.OrderDate.toISOString().substring(0, 7);
        const key = `${row.Country}|${row.CategoryName}|${month}`;

        if (!aggregated[key]) {
            aggregated[key] = {
                country: row.Country,
                category: row.CategoryName,
                month: month,
                revenue: 0,
                quantity: 0
            };
        }
        aggregated[key].revenue += row.TotalAmount || 0;
        aggregated[key].quantity += row.Quantity || 0;
    });

    // Convert to arrays for plotting
    const countries = Object.values(aggregated).map(d => d.country);
    const categories = Object.values(aggregated).map(d => d.category);
    const months = Object.values(aggregated).map(d => d.month);
    const revenues = Object.values(aggregated).map(d => d.revenue);

    // Create unique indices for countries and categories
    const uniqueCountries = [...new Set(countries)];
    const uniqueCategories = [...new Set(categories)];

    const countryIndices = countries.map(c => uniqueCountries.indexOf(c));
    const categoryIndices = categories.map(c => uniqueCategories.indexOf(c));
    const monthIndices = months.map(m => new Date(m).getTime());

    const trace = {
        x: countryIndices,
        y: categoryIndices,
        z: monthIndices,
        mode: 'markers',
        type: 'scatter3d',
        marker: {
            size: revenues.map(r => Math.sqrt(r) / 10),
            color: revenues,
            colorscale: 'Viridis',
            showscale: true,
            colorbar: {
                title: 'Revenue ($)',
                thickness: 15,
                len: 0.7
            },
            line: {
                color: '#1a1f2e',
                width: 0.5
            }
        },
        text: Object.values(aggregated).map(d =>
            `Country: ${d.country}<br>Category: ${d.category}<br>Month: ${d.month}<br>Revenue: $${d.revenue.toFixed(2)}`
        ),
        hoverinfo: 'text'
    };

    const layout = {
        scene: {
            xaxis: {
                title: 'Country',
                ticktext: uniqueCountries,
                tickvals: [...Array(uniqueCountries.length).keys()],
                backgroundcolor: '#1a1f2e',
                gridcolor: '#3a4152',
                showbackground: true,
                color: '#9aa0a6'
            },
            yaxis: {
                title: 'Category',
                ticktext: uniqueCategories,
                tickvals: [...Array(uniqueCategories.length).keys()],
                backgroundcolor: '#1a1f2e',
                gridcolor: '#3a4152',
                showbackground: true,
                color: '#9aa0a6'
            },
            zaxis: {
                title: 'Time',
                backgroundcolor: '#1a1f2e',
                gridcolor: '#3a4152',
                showbackground: true,
                color: '#9aa0a6'
            },
            bgcolor: '#1a1f2e'
        },
        plot_bgcolor: '#1a1f2e',
        paper_bgcolor: '#242b3d',
        font: { color: '#e8eaed' },
        margin: { l: 0, r: 0, t: 0, b: 0 }
    };

    Plotly.newPlot('scatter3dChart', [trace], layout, { responsive: true });
}

function create3DSurfaceChart() {
    // Create 3D surface plot: Revenue by Country x Category
    const countrySales = {};
    const categorySales = {};

    // Get top 10 countries and all categories
    filteredData.forEach(row => {
        if (!countrySales[row.Country]) {
            countrySales[row.Country] = 0;
        }
        countrySales[row.Country] += row.TotalAmount || 0;
    });

    const topCountries = Object.entries(countrySales)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10)
        .map(item => item[0]);

    const categories = [...new Set(filteredData.map(row => row.CategoryName))].sort();

    // Create matrix for surface plot
    const zMatrix = [];

    topCountries.forEach(country => {
        const row = [];
        categories.forEach(category => {
            const revenue = filteredData
                .filter(r => r.Country === country && r.CategoryName === category)
                .reduce((sum, r) => sum + (r.TotalAmount || 0), 0);
            row.push(revenue);
        });
        zMatrix.push(row);
    });

    const trace = {
        z: zMatrix,
        x: categories,
        y: topCountries,
        type: 'surface',
        colorscale: 'Portland',
        showscale: true,
        colorbar: {
            title: 'Revenue ($)',
            thickness: 15,
            len: 0.7
        },
        contours: {
            z: {
                show: true,
                usecolormap: true,
                highlightcolor: '#42f462',
                project: { z: true }
            }
        }
    };

    const layout = {
        scene: {
            xaxis: {
                title: 'Category',
                backgroundcolor: '#1a1f2e',
                gridcolor: '#3a4152',
                showbackground: true,
                color: '#9aa0a6'
            },
            yaxis: {
                title: 'Country',
                backgroundcolor: '#1a1f2e',
                gridcolor: '#3a4152',
                showbackground: true,
                color: '#9aa0a6'
            },
            zaxis: {
                title: 'Revenue ($)',
                backgroundcolor: '#1a1f2e',
                gridcolor: '#3a4152',
                showbackground: true,
                color: '#9aa0a6'
            },
            bgcolor: '#1a1f2e',
            camera: {
                eye: { x: 1.5, y: 1.5, z: 1.3 }
            }
        },
        plot_bgcolor: '#1a1f2e',
        paper_bgcolor: '#242b3d',
        font: { color: '#e8eaed' },
        margin: { l: 0, r: 0, t: 0, b: 0 }
    };

    Plotly.newPlot('surface3dChart', [trace], layout, { responsive: true });
}

function create3DBarChart() {
    // Create 3D bar chart: Top products by Revenue x Quantity x Order Count
    const productStats = {};

    filteredData.forEach(row => {
        if (!productStats[row.ProductName]) {
            productStats[row.ProductName] = {
                revenue: 0,
                quantity: 0,
                orders: new Set()
            };
        }
        productStats[row.ProductName].revenue += row.TotalAmount || 0;
        productStats[row.ProductName].quantity += row.Quantity || 0;
        productStats[row.ProductName].orders.add(row.OrderID);
    });

    // Get top 15 products by revenue
    const topProducts = Object.entries(productStats)
        .sort((a, b) => b[1].revenue - a[1].revenue)
        .slice(0, 15);

    const products = topProducts.map(item => item[0]);
    const revenues = topProducts.map(item => item[1].revenue);
    const quantities = topProducts.map(item => item[1].quantity);
    const orderCounts = topProducts.map(item => item[1].orders.size);

    const trace = {
        x: revenues,
        y: quantities,
        z: orderCounts,
        mode: 'markers+text',
        type: 'scatter3d',
        marker: {
            size: 12,
            color: revenues,
            colorscale: 'Jet',
            showscale: true,
            colorbar: {
                title: 'Revenue ($)',
                thickness: 15,
                len: 0.7
            },
            line: {
                color: '#1a1f2e',
                width: 1
            },
            opacity: 0.8
        },
        text: products.map((p, i) => `${p.substring(0, 15)}...`),
        textposition: 'top center',
        textfont: {
            size: 8,
            color: '#e8eaed'
        },
        hovertext: products.map((p, i) =>
            `Product: ${p}<br>Revenue: $${revenues[i].toFixed(2)}<br>Quantity: ${quantities[i]}<br>Orders: ${orderCounts[i]}`
        ),
        hoverinfo: 'text'
    };

    const layout = {
        scene: {
            xaxis: {
                title: 'Revenue ($)',
                backgroundcolor: '#1a1f2e',
                gridcolor: '#3a4152',
                showbackground: true,
                color: '#9aa0a6'
            },
            yaxis: {
                title: 'Quantity Sold',
                backgroundcolor: '#1a1f2e',
                gridcolor: '#3a4152',
                showbackground: true,
                color: '#9aa0a6'
            },
            zaxis: {
                title: 'Order Count',
                backgroundcolor: '#1a1f2e',
                gridcolor: '#3a4152',
                showbackground: true,
                color: '#9aa0a6'
            },
            bgcolor: '#1a1f2e',
            camera: {
                eye: { x: 1.7, y: 1.7, z: 1.3 }
            }
        },
        plot_bgcolor: '#1a1f2e',
        paper_bgcolor: '#242b3d',
        font: { color: '#e8eaed' },
        margin: { l: 0, r: 0, t: 0, b: 0 }
    };

    Plotly.newPlot('bar3dChart', [trace], layout, { responsive: true });
}

// ============================================================================
// DATA TABLE
// ============================================================================

function updateDataTable() {
    // Get recent transactions (top 20)
    const recent = [...filteredData]
        .sort((a, b) => b.OrderDate - a.OrderDate)
        .slice(0, 20);

    const tbody = document.getElementById('transactionsBody');
    tbody.innerHTML = '';

    recent.forEach(row => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${row.OrderID}</td>
            <td>${row.OrderDate.toISOString().split('T')[0]}</td>
            <td>${row.CompanyName}</td>
            <td>${row.ProductName}</td>
            <td>${row.Quantity}</td>
            <td>$${(row.UnitPrice || 0).toFixed(2)}</td>
            <td>$${(row.TotalAmount || 0).toFixed(2)}</td>
        `;
        tbody.appendChild(tr);
    });

    // Update summary statistics
    const kpis = calculateKPIs();
    const statsBody = document.getElementById('statsBody');
    statsBody.innerHTML = `
        <tr>
            <td>Total Revenue</td>
            <td>$${kpis.totalRevenue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
        </tr>
        <tr>
            <td>Average Revenue</td>
            <td>$${(filteredData.reduce((sum, row) => sum + row.TotalAmount, 0) / Math.max(filteredData.length, 1)).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
        </tr>
        <tr>
            <td>Min Transaction</td>
            <td>$${Math.min(...filteredData.map(row => row.TotalAmount)).toFixed(2)}</td>
        </tr>
        <tr>
            <td>Max Transaction</td>
            <td>$${Math.max(...filteredData.map(row => row.TotalAmount)).toFixed(2)}</td>
        </tr>
        <tr>
            <td>Std Deviation</td>
            <td>$${kpis.stdDev.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
        </tr>
    `;
}

// ============================================================================
// DASHBOARD UPDATE
// ============================================================================

function updateDashboard() {
    updateKPIs();
    createSalesTrendChart();
    createCountriesChart();
    createProductsChart();
    createCategoryChart();
    createCustomersChart();
    createMonthlyChart();
    create3DScatterChart();
    create3DSurfaceChart();
    create3DBarChart();
    updateDataTable();
    updateDateRangeDisplay();
}

function updateDateRangeDisplay() {
    const startDate = new Date(document.getElementById('startDate').value);
    const endDate = new Date(document.getElementById('endDate').value);

    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    const startStr = startDate.toLocaleDateString('en-US', options);
    const endStr = endDate.toLocaleDateString('en-US', options);

    document.getElementById('dateRange').textContent = `Dashboard Period: ${startStr} → ${endStr}`;
}

// ============================================================================
// FILTER UI SETUP
// ============================================================================

function setupFilters() {
    // Set date range
    const dates = factSales.map(row => row.OrderDate).filter(d => d);
    const minDate = new Date(Math.min(...dates));
    const maxDate = new Date(Math.max(...dates));

    document.getElementById('startDate').value = minDate.toISOString().split('T')[0];
    document.getElementById('endDate').value = maxDate.toISOString().split('T')[0];

    // Setup country filter
    const countries = [...new Set(dimCustomers.map(c => c.Country))].sort();
    const countryList = document.getElementById('countryList');

    countries.forEach(country => {
        const label = document.createElement('label');
        label.className = 'checkbox-label';
        label.innerHTML = `
            <input type="checkbox" value="${country}" checked>
            <span>${country}</span>
        `;
        countryList.appendChild(label);
    });

    // Setup category filter
    const categories = [...new Set(dimProducts.map(p => p.CategoryName))].sort();
    const categoryList = document.getElementById('categoryList');

    categories.forEach(category => {
        const label = document.createElement('label');
        label.className = 'checkbox-label';
        label.innerHTML = `
            <input type="checkbox" value="${category}" checked>
            <span>${category}</span>
        `;
        categoryList.appendChild(label);
    });

    // Setup event listeners
    document.getElementById('allCountries').addEventListener('change', (e) => {
        const countryList = document.getElementById('countryList');
        if (e.target.checked) {
            countryList.style.display = 'none';
            countryList.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = true);
        } else {
            countryList.style.display = 'block';
        }
        applyFilters();
    });

    document.getElementById('allCategories').addEventListener('change', (e) => {
        const categoryList = document.getElementById('categoryList');
        if (e.target.checked) {
            categoryList.style.display = 'none';
            categoryList.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = true);
        } else {
            categoryList.style.display = 'block';
        }
        applyFilters();
    });

    document.getElementById('startDate').addEventListener('change', applyFilters);
    document.getElementById('endDate').addEventListener('change', applyFilters);

    document.getElementById('refreshBtn').addEventListener('click', () => {
        location.reload();
    });

    // Add change listeners to checkboxes
    countryList.addEventListener('change', applyFilters);
    categoryList.addEventListener('change', applyFilters);
}

// ============================================================================
// INITIALIZATION
// ============================================================================

async function init() {
    console.log('Initializing dashboard...');

    const loaded = await loadAllData();

    if (loaded) {
        setupFilters();
        applyFilters();

        // Update last updated time
        document.getElementById('lastUpdated').textContent =
            `Last Updated: ${new Date().toLocaleString('en-US', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            })}`;

        console.log('Dashboard initialized successfully');
    }
}

// Start the application when DOM is ready
document.addEventListener('DOMContentLoaded', init);
