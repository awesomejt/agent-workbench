package cmd

import (
	"fmt"
	"os"
	"strings"
	"time"

	"agent-workbench/cli/internal/api"
	"agent-workbench/cli/internal/render"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var exportTodoCmd = &cobra.Command{
	Use:   "todo",
	Short: "Export tasks as a TODO.md file",
	Long: `Generate a TODO.md file from the project's task list.

AWB remains the source of truth. This file is a read-only snapshot useful for
public repos, GitHub issue tracking, or collaborators without API access.

Example:
  awb export todo
  awb export todo --output TASKS.md`,
	RunE: func(cmd *cobra.Command, args []string) error {
		slug, err := requireFlag(cmd, "project")
		if err != nil {
			return err
		}

		output, _ := cmd.Flags().GetString("output")

		client := newClient()
		project, err := client.ProjectBySlug(slug)
		if err != nil {
			return render.Err("resolve project: %v", err)
		}

		tasks, err := listAllTasks(client, project.ID)
		if err != nil {
			return render.Err("list tasks: %v", err)
		}

		md := buildTodoMarkdown(project, tasks, viper.GetString("api_url"))

		if output == "-" {
			fmt.Print(md)
			return nil
		}
		if err := os.WriteFile(output, []byte(md), 0o644); err != nil {
			return render.Err("write file: %v", err)
		}
		render.Line("wrote %s (%d tasks)", output, len(tasks))
		return nil
	},
}

func init() {
	exportCmd.AddCommand(exportTodoCmd)
	exportTodoCmd.Flags().String("output", "TODO.md", "Output file path (use - for stdout)")
}

// phaseOrder defines the canonical display order for task phases.
var phaseOrder = []string{"discovery", "design", "implementation", "testing", "review"}

func buildTodoMarkdown(project api.Project, tasks []api.Task, apiURL string) string {
	var sb strings.Builder

	sb.WriteString(fmt.Sprintf("# %s\n\n", project.Name))
	sb.WriteString(fmt.Sprintf(
		"> Exported from Agent Workbench on %s."+
			" AWB is the source of truth — run `awb export todo` to regenerate.\n",
		time.Now().UTC().Format("2006-01-02"),
	))
	sb.WriteString(fmt.Sprintf("> Project: `%s` · API: %s\n\n", project.Slug, apiURL))

	// Group tasks by phase.
	byPhase := make(map[string][]api.Task)
	for _, t := range tasks {
		byPhase[t.Phase] = append(byPhase[t.Phase], t)
	}

	// Emit phases in canonical order; append any unknown phases at the end.
	known := make(map[string]bool)
	for _, ph := range phaseOrder {
		known[ph] = true
	}
	phases := append([]string{}, phaseOrder...)
	for ph := range byPhase {
		if !known[ph] {
			phases = append(phases, ph)
		}
	}

	wrote := false
	for _, ph := range phases {
		phaseTasks, ok := byPhase[ph]
		if !ok {
			continue
		}
		if wrote {
			sb.WriteString("\n")
		}
		sb.WriteString(fmt.Sprintf("## %s\n\n", ph))
		for _, t := range phaseTasks {
			check := todoCheck(t.Status)
			sb.WriteString(fmt.Sprintf("- %s %s", check, t.Title))
			if t.Priority != 0 {
				sb.WriteString(fmt.Sprintf(" _(priority: %d)_", t.Priority))
			}
			sb.WriteString("\n")
			if t.Description != nil && *t.Description != "" {
				// Indent description under the list item.
				for _, line := range strings.Split(strings.TrimRight(*t.Description, "\n"), "\n") {
					sb.WriteString(fmt.Sprintf("  %s\n", line))
				}
			}
		}
		wrote = true
	}

	return sb.String()
}

func todoCheck(status string) string {
	switch status {
	case "completed":
		return "[x]"
	case "blocked":
		return "[~]"
	default:
		return "[ ]"
	}
}
