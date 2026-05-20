import { Navigate } from "react-router-dom";
import { getToken, isTokenExpired } from "../lib/auth";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = getToken();
  if (!token || isTokenExpired(token)) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

export default ProtectedRoute;