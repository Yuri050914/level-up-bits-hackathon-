async function signup(username, password) {
    const response = await fetch("http://localhost:8000/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
    });

    const data = await response.json();
    if (response.ok) {
        alert("Signup successful!");
    } else {
        alert(data.detail);
    }
}
