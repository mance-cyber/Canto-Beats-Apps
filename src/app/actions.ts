"use server";

import { generateUniqueLicenseKey } from "@/ai/flows/generate-unique-license-key";

export async function getLicenseKey(sessionId: string) {
  if (!sessionId) {
    console.error("getLicenseKey called without sessionId");
    throw new Error("需要一個有效的 Session ID。");
  }

  // In a real application, you would validate the session ID with Stripe
  // and retrieve customer details like email.
  // For this demo, we'll simulate this process.
  console.log(`Generating license key for session ID: ${sessionId}`);

  try {
    const result = await generateUniqueLicenseKey({
      sessionId,
      email: "demo-user@example.com", // Placeholder email
    });

    if (!result.licenseKey) {
        throw new Error("AI did not return a license key.");
    }
    
    // In a real application, you would save the license key to Firestore here,
    // associated with the user/email and session ID.
    // e.g., await db.collection('licenses').add({ ... });
    // Also, trigger the "Trigger Email" extension to send the key to the user.

    console.log(`Generated license key: ${result.licenseKey}`);
    return result.licenseKey;
  } catch (error) {
    console.error("Error generating license key:", error);
    // Return a user-friendly error message
    throw new Error("生成 License Key 失敗，請聯絡客戶服務。");
  }
}
