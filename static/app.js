
async function fetchProducts() {
  try {
    const res = await fetch("http://localhost:5000/products");
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
          ${p.image_url ? `<img src="http://localhost:5000/${p.image_url}" width="100"/>` : ''}
        `;
        section.appendChild(div);
      });
      container.appendChild(section);
    }
  } catch (error) {
    console.error("Failed to load products:", error);
  }
}

async function fetchAndDisplayCategories() {
  const token = localStorage.getItem("token");
  if (!token) return;

  try {
    const res = await fetch("http://localhost:5000/categories", {
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
  }
}

function addCategory() {
  const name = document.getElementById("newCategory").value;
  const token = localStorage.getItem("token");
  if (!name || !token) return;

  fetch("http://localhost:5000/categories", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({ name })
  })
    .then(res => res.json())
    .then(data => {
      alert(data.message);
      fetchAndDisplayCategories();
    })
    .catch(err => console.error("Error adding category", err));
}

function deleteCategory(id) {
  const token = localStorage.getItem("token");
  if (!token) return;

  fetch(`http://localhost:5000/categories/${id}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`
    }
  })
    .then(res => res.json())
    .then(data => {
      alert(data.message);
      fetchAndDisplayCategories();
    })
    .catch(err => console.error("Error deleting category", err));
}

function login() {
  const username = prompt("Username:");
  const password = prompt("Password:");
  fetch("http://localhost:5000/api/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password })
  })
    .then(res => res.json())
    .then(data => {
      if (data.access_token) {
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("role", data.role);
        alert(`Logged in as ${data.role}`);
        if (data.role === 'admin') {
          document.getElementById("addProductSection").style.display = "block";
          document.getElementById("manageCategories").style.display = "block";
          fetchAndDisplayCategories();
        }
      } else {
        alert("Login failed");
      }
    })
    .catch(err => alert("Error logging in"));
}

function register() {
  const username = prompt("Username:");
  const password = prompt("Password:");
  fetch("http://localhost:5000/api/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password })
  })
    .then(res => res.json())
    .then(data => alert(data.message || "Error"))
    .catch(err => alert("Error registering"));
}

document.getElementById("addProductForm").addEventListener("submit", async function (e) {
  e.preventDefault();
  const form = e.target;
  const formData = new FormData(form);

  const token = localStorage.getItem("token");
  if (!token) {
    alert("Unauthorized");
    return;
  }

  try {
    const res = await fetch("http://localhost:5000/add-product", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`
      },
      body: formData
    });
    const data = await res.json();
    alert(data.message);
    fetchProducts();
    form.reset();
  } catch (err) {
    alert("Error adding product");
    console.error(err);
  }
});

document.getElementById("categoryFilter").addEventListener("change", fetchProducts);

fetchProducts();
