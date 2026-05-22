export const getToken = (): string | null =>
  localStorage.getItem("app_token");

export const isTokenExpired = (token: string): boolean => {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.exp * 1000 < Date.now();
  } catch {
    return true;
  }
};

export const logout = (): void => {
  localStorage.removeItem("app_token");
  window.location.href = "/login";
};