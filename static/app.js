const BASE_URL = "https://gym-suppliments.onrender.com";

// Fetch and display products
async function fetchProducts() {
  try {
    const res = await fetch(`${BASE_URL}/products`);
    const products = await res.json();
    const container = document.getElementById("products");
    const filterValue = document.getElementById("categoryFilter").value;
    container.innerHTML = "";

    const categories = new Set();
    const grouped = {};
    products.forEach(p => {
      categories.add(p.category);
      if (!grouped[p.category]) grouped[p.category] = [];
      grouped[p.category].push(p);
    });

    const categorySelect = document.getElementById("categoryFilter");
    categorySelect.innerHTML = '<option value="">All</option>';
    [...categories].forEach(cat => {
      const opt = document.createElement("option");
      opt.value = cat;
      opt.textContent = cat;
      categorySelect.appendChild(opt);
    });
    categorySelect.value = filterValue;

    for (const category in grouped) {
      if (filterValue && category !== filterValue) continue;
      const section = document.createElement("section");
      section.innerHTML = `<h3>${category}</h3>`;
      grouped[category].forEach(p => {
        const div = document.createElement("div");
        div.className = "product";
        div.innerHTML = `
          <h4>${p.name}</h4>
          <p>$${p.price}</p>
          ${p.image_url ? `<img src="${BASE_URL}/${p.image_url}" width="100"/>` : ''}
        `;
        section.appendChild(div);
      });
      container.appendChild(section);
    }
  } catch (error) {
    console.error("Failed to load products:", error);
    showToast("Error loading products");
  }
}

// Fetch and display categories
async function fetchAndDisplayCategories() {
  const token = localStorage.getItem("token");
  if (!token) return;

  try {
    const res = await fetch(`${BASE_URL}/categories`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    const categories = await res.json();
    const container = document.getElementById("manageCategories");
    container.innerHTML = `<h2>Manage Categories (Admin)</h2>
      <input type="text" id="newCategory" placeholder="New Category">
      <button onclick="addCategory()">Add Category</button>`;

    categories.forEach(cat => {
      const div = document.createElement("div");
      div.innerHTML = `${cat.name} <button onclick="deleteCategory(${cat.id})">Delete</button>`;
      container.appendChild(div);
    });
  } catch (err) {
    console.error("Error loading categories", err);
    showToast("Error loading categories");
  }
}

// Add new category
function addCategory() {
  const name = document.getElementById("newCategory").value;
  const token = localStorage.getItem("token");
  if (!name || !token) return;

  fetch(`${BASE_URL}/categories`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({ name })
  })
    .then(res => res.json())
    .then(data => {
      showToast(data.message);
      fetchAndDisplayCategories();
    })
    .catch(err => {
      console.error("Error adding category", err);
      showToast("Error adding category");
    });
}

// Delete category
function deleteCategory(id) {
  const token = localStorage.getItem("token");
  if (!token) return;

  fetch(`${BASE_URL}/categories/${id}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` }
  })
    .then(res => res.json())
    .then(data => {
      showToast(data.message);
      fetchAndDisplayCategories();
    })
    .catch(err => {
      console.error("Error deleting category", err);
      showToast("Error deleting category");
    });
}

// Redirect to login page
function login() {
  window.location.href = "/login";
}

// Redirect to register page
function register() {
  window.location.href = "/register";
}

// Handle Add Product form submission
document.getElementById("addProductForm").addEventListener("submit", async function (e) {
  e.preventDefault();
  const form = e.target;
  const formData = new FormData(form);
  const token = localStorage.getItem("token");

  if (!token) {
    showToast("Unauthorized");
    return;
  }

  try {
    const res = await fetch(`${BASE_URL}/add-product`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: formData
    });
    const data = await res.json();
    showToast(data.message);
    fetchProducts();
    form.reset();
  } catch (err) {
    console.error("Error adding product", err);
    showToast("Error adding product");
  }
});

// Filter products by category
document.getElementById("categoryFilter").addEventListener("change", fetchProducts);

// Initial load
fetchProducts();
