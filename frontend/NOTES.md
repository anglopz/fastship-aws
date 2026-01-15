# Frontend Development Notes

## Known Issues

### 1. Next.js vs React Router Compatibility

Some components use Next.js-specific APIs that need alternatives for React Router:

- **`useFormStatus`** (in `app/components/ui/submit-button.tsx`): 
  - This is a Next.js Server Actions API that doesn't exist in React Router
  - **Temporary Fix**: The component will error if used without a form action
  - **Solution**: Replace with React state management or React Router form handling
  
- **`next-themes`**: Installed but may need configuration for React Router context

### 2. TypeScript Warnings

Non-blocking TypeScript warnings:
- Unused imports (cleanup recommended)
- Missing type definitions for some packages
- These don't prevent the dev server from running

### 3. Windows/WSL Path Warnings

Harmless warnings during `npm install` due to Windows/WSL path handling.
These don't affect functionality.

## Development

The dev server runs successfully on http://localhost:5173 despite these warnings.
