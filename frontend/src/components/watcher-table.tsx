import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { getWatchedMessages } from "@/lib/admin-api";

export async function WatcherTable() {
  const messages = await getWatchedMessages();

  if (messages.length === 0) {
    return <p className="text-sm text-muted-foreground">No watched messages yet.</p>;
  }

  return (
    <div className="overflow-x-auto rounded-2xl border border-border/60">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Channel</TableHead>
            <TableHead>Author</TableHead>
            <TableHead>Content</TableHead>
            <TableHead>Created</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {messages.map((message) => (
            <TableRow key={message.id}>
              <TableCell className="font-medium">#{message.channel_name}</TableCell>
              <TableCell>{message.author}</TableCell>
              <TableCell className="max-w-xs truncate">{message.content}</TableCell>
              <TableCell className="text-mono-tabular text-muted-foreground">
                {new Date(message.created_at).toLocaleString()}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
