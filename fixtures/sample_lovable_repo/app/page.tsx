// Synthetic Lovable-generated page with a few smells for the demo audit.
import { useState } from "react";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, "anon-key");

export default function Home() {
  const [count, setCount] = useState(0);

  // TODO: replace with real booking widget
  // @ts-ignore
  const handle = (e: any) => {
    console.log("clicked", e);
    try {
      supabase.from("page_views").insert({ user_id: 1 });
    } catch (e) {}
    setCount(count + 1);
  };

  return (
    <main>
      <div dangerouslySetInnerHTML={{ __html: "<h1>Hi</h1>" }} />
      <button onClick={handle}>Click me ({count})</button>
    </main>
  );
}
