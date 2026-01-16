import { RotateCw } from "lucide-react";
import { Button } from "./button";

interface SubmitButtonProps {
  text: string;
  pending?: boolean;
  disabled?: boolean;
}

function SubmitButton({ text, pending = false, disabled = false }: SubmitButtonProps) {
  return (
    <Button 
      type="submit" 
      className="w-full" 
      disabled={pending || disabled}
    >
      {pending ? (
        <>
          <RotateCw className="mr-2 h-4 w-4 animate-spin" />
          <span>Loading...</span>
        </>
      ) : text}
    </Button>
  )
}

export { SubmitButton }