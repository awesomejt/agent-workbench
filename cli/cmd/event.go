package cmd

import (
	"agent-workbench/cli/internal/render"
	"encoding/json"
	"fmt"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var eventCmd = &cobra.Command{
	Use:   "event",
	Short: "List and append project events",
}

var eventListCmd = &cobra.Command{
	Use:   "list",
	Short: "List recent events for a project",
	RunE: func(cmd *cobra.Command, args []string) error {
		slug, err := requireFlag(cmd, "project")
		if err != nil {
			return err
		}
		limit, _ := cmd.Flags().GetInt("limit")

		client := newClient()
		project, err := client.ProjectBySlug(slug)
		if err != nil {
			return render.Err("resolve project: %v", err)
		}

		list, err := client.ListEvents(project.ID, 1, limit)
		if err != nil {
			return render.Err("list events: %v", err)
		}

		if viper.GetString("output") == "json" {
			return render.JSON(list)
		}

		if len(list.Items) == 0 {
			fmt.Println("no events found")
			return nil
		}

		rows := make([][]string, len(list.Items))
		for i, e := range list.Items {
			rows[i] = []string{
				e.ID[:8],
				e.EventType,
				render.Str(e.ActorName, "-"),
				render.Str(e.TaskID, "-"),
				render.Str(e.RunID, "-"),
				e.CreatedAt,
			}
		}
		render.Table([]string{"ID", "TYPE", "ACTOR", "TASK", "RUN", "CREATED"}, rows)
		render.Line("\n%d event(s) — page %d of %d", list.Total, list.Page, list.Pages)
		return nil
	},
}

var eventAppendCmd = &cobra.Command{
	Use:   "append",
	Short: "Append a custom event to the audit trail",
	RunE: func(cmd *cobra.Command, args []string) error {
		slug, err := requireFlag(cmd, "project")
		if err != nil {
			return err
		}
		eventType, _ := cmd.Flags().GetString("type")
		if eventType == "" {
			return render.Err("--type is required")
		}

		taskID, _ := cmd.Flags().GetString("task")
		runID, _ := cmd.Flags().GetString("run")
		actorName, _ := cmd.Flags().GetString("actor-name")
		actorType, _ := cmd.Flags().GetString("actor-type")
		payloadStr, _ := cmd.Flags().GetString("payload")

		client := newClient()
		project, err := client.ProjectBySlug(slug)
		if err != nil {
			return render.Err("resolve project: %v", err)
		}

		body := map[string]any{
			"project_id": project.ID,
			"event_type": eventType,
		}
		if taskID != "" {
			body["task_id"] = taskID
		}
		if runID != "" {
			body["run_id"] = runID
		}
		if actorName != "" {
			body["actor_name"] = actorName
		}
		if actorType != "" {
			body["actor_type"] = actorType
		}
		if payloadStr != "" {
			var payload any
			if err := json.Unmarshal([]byte(payloadStr), &payload); err != nil {
				return render.Err("--payload must be valid JSON: %v", err)
			}
			body["payload"] = payload
		}

		event, err := client.AppendEvent(body)
		if err != nil {
			return render.Err("append event: %v", err)
		}

		if viper.GetString("output") == "json" {
			return render.JSON(event)
		}
		render.Line("event %s (%s) created at %s", event.ID[:8], event.EventType, event.CreatedAt)
		return nil
	},
}

func init() {
	rootCmd.AddCommand(eventCmd)
	eventCmd.AddCommand(eventListCmd)
	eventCmd.AddCommand(eventAppendCmd)

	eventListCmd.Flags().Int("limit", 50, "Maximum number of events to show")

	eventAppendCmd.Flags().String("type", "", "Event type (required)")
	eventAppendCmd.Flags().String("task", "", "Task ID to associate with this event")
	eventAppendCmd.Flags().String("run", "", "Run ID to associate with this event")
	eventAppendCmd.Flags().String("actor-name", "", "Actor name (e.g. agent name)")
	eventAppendCmd.Flags().String("actor-type", "agent", "Actor type (agent or human)")
	eventAppendCmd.Flags().String("payload", "", "JSON payload string (e.g. '{\"key\":\"value\"}')")
}
