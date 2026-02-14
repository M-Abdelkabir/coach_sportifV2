import { AppProvider } from "@/lib/app-context";
import { FitnessApp } from "@/components/fitness/fitness-app";

export default function Page() {
  return (
    <AppProvider>
      <FitnessApp />
    </AppProvider>
  );
}
