// This is your test publishable API key.
const stripe = Stripe("pk_test_51Sb5n51M7N6QXWCoKe7MJafuyH8K097vox8mTW6JRfL6Pv79fkylP7tPXAhFIc2t6cgEQaDMHmdlq1VmevDIJyz300wDXf0SNf");

initialize();

// Create a Checkout Session
async function initialize() {
  const fetchClientSecret = async () => {
    const response = await fetch("/create-checkout-session", {
      method: "POST",
    });
    const { clientSecret } = await response.json();
    return clientSecret;
  };

  const checkout = await stripe.initEmbeddedCheckout({
    fetchClientSecret,
  });

  // Mount Checkout
  checkout.mount('#checkout');
}