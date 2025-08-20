<?php
// /var/www/html/index.php

// Check if email file exists
$emailFile = '/var/www/appdata/email';
$emailExists = file_exists($emailFile);
$showLoginForm = !$emailExists;
$errorMessage = '';

// Handle form submission
if ($_POST && isset($_POST['email'])) {
    $email = trim($_POST['email']);
    
    // Simple email validation (something@something.som)
    if (filter_var($email, FILTER_VALIDATE_EMAIL)) {
        // Create the email file and write the email
        if (file_put_contents($emailFile, $email) !== false) {
            $showLoginForm = false;
            $emailExists = true;
        } else {
            $errorMessage = 'Error saving email. Please try again.';
        }
    } else {
        $errorMessage = 'Please enter a valid email address.';
    }
}

// If we need to show login form, display it and exit
if ($showLoginForm) {
?>
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>The Midnight Café - Login</title>
<link rel="stylesheet" href="/styles/midnight.css">
</head>
<body>
<div class="site">
  <header class="hero">
    <h1>☕ The Midnight Café</h1>
    <p class="tagline">Neo-Tokyo · Open 00:00 — 06:00 · Where digital dreams brew</p>
  </header>
  <main class="content">
    <section class="card">
      <h2>Welcome to The Midnight Café</h2>
      <p>Please enter your registered email address to access the café.</p>
      
      <?php if ($errorMessage): ?>
        <div class="error" style="color: #ff6b6b; margin: 10px 0; padding: 10px; border: 1px solid #ff6b6b; border-radius: 4px; background: rgba(255, 107, 107, 0.1);">
          <?php echo htmlspecialchars($errorMessage); ?>
        </div>
      <?php endif; ?>
      
      <form method="post" action="">
        <div style="margin: 20px 0;">
          <label for="email" style="display: block; margin-bottom: 5px;">Email Address:</label>
          <input type="email" id="email" name="email" required 
                 style="width: 100%; max-width: 300px; padding: 10px; border: 1px solid #333; border-radius: 4px; background: #1a1a1a; color: #fff;"
                 placeholder="your.email@example.com"
                 value="<?php echo isset($_POST['email']) ? htmlspecialchars($_POST['email']) : ''; ?>">
        </div>
        <button type="submit" style="padding: 10px 20px; background: #4a4a4a; color: #fff; border: none; border-radius: 4px; cursor: pointer;">
          Enter Café
        </button>
      </form>
    </section>
  </main>
  <footer class="footer">
    <small>© 2045 Midnight Café — Neon & Protocols</small>
  </footer>
</div>
</body>
</html>
<?php
    exit;
}
?>
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>The Midnight Café</title>
<link rel="stylesheet" href="/styles/midnight.css">
</head>
<body>
<div class="site">
  <header class="hero">
    <h1>☕ The Midnight Café</h1>
    <p class="tagline">Neo-Tokyo · Open 00:00 — 06:00 · Where digital dreams brew</p>
  </header>
  <main class="content">
    <section class="card">
      <h2>Tonight's Specials</h2>
      <ul>
        <li><a href="/coffee_menu/">View the Coffee Menu</a></li>
        <li><a href="/order.php">Place an Online Order</a></li>
      </ul>
      <p class="hint">Tip: Staff sometimes leave notes in their shift files.</p>
    </section>
    <section class="card">
      <h2>For curious wanderers</h2>
      <p>We brew different blends. Some recipes are for registered staff only.</p>
      <p class="small">If you're testing the site, try the order system — it's still in beta.</p>
    </section>
  </main>
  <footer class="footer">
    <small>© 2045 Midnight Café — Neon & Protocols</small>
  </footer>
</div>
</body>
</html>
