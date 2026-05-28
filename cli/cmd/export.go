package cmd

import (
	"agent-workbench/cli/internal/api"

	"github.com/spf13/cobra"
)

var exportCmd = &cobra.Command{
	Use:   "export",
	Short: "Export project tasks to a file",
	Long: `Export project tasks from Agent Workbench to a portable file.

Subcommands:
  todo   Generate a TODO.md (useful for public repos or offline review)
  yaml   Generate a structured YAML snapshot of the project and all tasks`,
}

func init() {
	rootCmd.AddCommand(exportCmd)
}

// listAllTasks pages through the API and returns every task for the project.
func listAllTasks(client *api.Client, projectID string) ([]api.Task, error) {
	var all []api.Task
	page := 1
	for {
		list, err := client.ListTasks(projectID, api.TaskListOpts{Page: page, PerPage: 100})
		if err != nil {
			return nil, err
		}
		all = append(all, list.Items...)
		if page >= list.Pages {
			break
		}
		page++
	}
	return all, nil
}
