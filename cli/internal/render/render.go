package render

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"text/tabwriter"
)

// JSON pretty-prints v to stdout.
func JSON(v any) error {
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	return enc.Encode(v)
}

// Table writes rows to stdout using tab-aligned columns.
// headers and each row must have the same number of fields.
func Table(headers []string, rows [][]string) {
	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintln(w, strings.Join(headers, "\t"))
	fmt.Fprintln(w, strings.Repeat("-\t", len(headers)))
	for _, row := range rows {
		fmt.Fprintln(w, strings.Join(row, "\t"))
	}
	w.Flush()
}

// Line writes a single formatted line to stdout.
func Line(format string, args ...any) {
	fmt.Printf(format+"\n", args...)
}

// Err returns a formatted error. Cobra prints the returned error to stderr,
// so this intentionally does not write to stderr itself.
func Err(format string, args ...any) error {
	return fmt.Errorf(format, args...)
}

// Str returns s if non-nil, otherwise the placeholder.
func Str(s *string, placeholder string) string {
	if s == nil {
		return placeholder
	}
	return *s
}
