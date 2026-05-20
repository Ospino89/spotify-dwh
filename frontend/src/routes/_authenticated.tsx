import { createFileRoute } from "@tanstack/react-router";
import { AuthenticatedLayout } from "@/components/Navbar";

export const Route = createFileRoute("/_authenticated")({
  component: AuthenticatedLayout,
});
