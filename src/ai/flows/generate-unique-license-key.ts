'use server';

/**
 * @fileOverview Generates a unique license key after successful payment.
 *
 * - generateUniqueLicenseKey - A function that generates a unique license key.
 * - GenerateUniqueLicenseKeyInput - The input type for the generateUniqueLicenseKey function.
 * - GenerateUniqueLicenseKeyOutput - The return type for the generateUniqueLicenseKey function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const GenerateUniqueLicenseKeyInputSchema = z.object({
  sessionId: z.string().describe('The Stripe checkout session ID.'),
  email: z.string().email().optional().describe('The user email address.'),
});
export type GenerateUniqueLicenseKeyInput = z.infer<typeof GenerateUniqueLicenseKeyInputSchema>;

const GenerateUniqueLicenseKeyOutputSchema = z.object({
  licenseKey: z.string().describe('The generated unique license key.'),
});
export type GenerateUniqueLicenseKeyOutput = z.infer<typeof GenerateUniqueLicenseKeyOutputSchema>;

export async function generateUniqueLicenseKey(
  input: GenerateUniqueLicenseKeyInput
): Promise<GenerateUniqueLicenseKeyOutput> {
  return generateUniqueLicenseKeyFlow(input);
}

const generateLicenseKeyPrompt = ai.definePrompt({
  name: 'generateLicenseKeyPrompt',
  prompt: 'Generate a unique 16-character license key in the format XXXX-XXXX-XXXX-XXXX.',
  output: {schema: GenerateUniqueLicenseKeyOutputSchema},
});

const generateUniqueLicenseKeyFlow = ai.defineFlow(
  {
    name: 'generateUniqueLicenseKeyFlow',
    inputSchema: GenerateUniqueLicenseKeyInputSchema,
    outputSchema: GenerateUniqueLicenseKeyOutputSchema,
  },
  async input => {
    const {output} = await generateLicenseKeyPrompt({});
    return {
      licenseKey: output!.licenseKey,
    };
  }
);
