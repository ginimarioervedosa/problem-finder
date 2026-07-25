// The one typed HTTP client. Every request goes through the generated
// openapi-typescript schema, so a backend contract change is a compile error.
import createClient from "openapi-fetch";

import type { paths } from "./schema";

const baseUrl: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const api = createClient<paths>({ baseUrl });
