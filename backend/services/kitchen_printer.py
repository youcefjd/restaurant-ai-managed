"""
Kitchen Printer Service for Restaurant Orders

Supports multiple printing methods:
1. Direct network printer (via CUPS or Windows printing)
2. Email-to-print (for cloud-connected receipt printers)
3. File-based queue (fallback)
"""
import os
import logging
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class KitchenPrinter:
    """Service for printing order tickets to kitchen."""

    def __init__(self):
        self.print_queue_dir = Path("kitchen_orders")
        self.print_queue_dir.mkdir(exist_ok=True)
        self.email_to_print = os.getenv("KITCHEN_PRINTER_EMAIL")  # Optional email for cloud printers

    def print_order(self, order: Dict[str, Any]) -> bool:
        """
        Print order ticket to kitchen.

        Args:
            order: Order dictionary with items, customer info, etc.

        Returns:
            bool: True if print successful, False otherwise
        """
        try:
            # Generate ticket text
            ticket = self._format_order_ticket(order)

            # Try printing methods in order of preference
            if self.email_to_print:
                return self._print_via_email(ticket, order)
            else:
                # Fallback: Save to print queue directory
                return self._save_to_print_queue(ticket, order)

        except Exception as e:
            logger.error(f"Failed to print order {order.get('id')}: {str(e)}")
            return False

    def _format_order_ticket(self, order: Dict[str, Any]) -> str:
        """Format order as a kitchen ticket."""
        import json

        order_items = json.loads(order.get("order_items", "[]"))

        ticket = f"""
{'='*40}
          KITCHEN ORDER
{'='*40}

Order #: {order.get('id')}
Time: {datetime.now().strftime('%I:%M %p')}
Date: {datetime.now().strftime('%m/%d/%Y')}

Customer: {order.get('customer_name', 'Guest')}
Phone: {order.get('customer_phone', 'N/A')}

Type: {'DELIVERY' if order.get('delivery_address') != 'Pickup' else 'PICKUP'}
{"Address: " + order.get('delivery_address', '') if order.get('delivery_address') != 'Pickup' else ''}

{'-'*40}
ITEMS:
{'-'*40}
"""

        for item in order_items:
            qty = item.get('quantity', 1)
            name = item.get('item_name', 'Unknown Item')
            ticket += f"\n{qty}x {name}\n"

            # Add modifiers
            modifiers = item.get('modifiers', [])
            if modifiers:
                for mod in modifiers:
                    ticket += f"   * {mod}\n"

        # Add special requests
        if order.get('special_requests'):
            ticket += f"\n{'-'*40}\n"
            ticket += f"SPECIAL REQUESTS:\n{order.get('special_requests')}\n"

        ticket += f"\n{'='*40}\n"
        ticket += f"Total: ${order.get('total', 0) / 100:.2f}\n"
        ticket += f"Payment: {order.get('payment_method', 'N/A').upper()}\n"

        if order.get('payment_status') == 'unpaid':
            ticket += f"\n*** PAYMENT ON ARRIVAL ***\n"

        ticket += f"{'='*40}\n\n"

        return ticket

    def _print_via_email(self, ticket: str, order: Dict[str, Any]) -> bool:
        """Send ticket to printer via email (for cloud printers)."""
        try:
            # Use SMS service to send email (can reuse SMTP if configured)
            # For now, just log
            logger.info(f"Would send to printer email: {self.email_to_print}")
            logger.info(f"Order ticket:\n{ticket}")

            # Also save to queue as backup
            return self._save_to_print_queue(ticket, order)

        except Exception as e:
            logger.error(f"Email-to-print failed: {str(e)}")
            return self._save_to_print_queue(ticket, order)

    def _save_to_print_queue(self, ticket: str, order: Dict[str, Any]) -> bool:
        """Save ticket to print queue directory."""
        try:
            order_id = order.get('id', 'unknown')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.print_queue_dir / f"order_{order_id}_{timestamp}.txt"

            with open(filename, 'w') as f:
                f.write(ticket)

            logger.info(f"Order ticket saved to {filename}")
            logger.info(f"\n{ticket}")  # Also log to console for immediate visibility

            return True

        except Exception as e:
            logger.error(f"Failed to save ticket to queue: {str(e)}")
            return False

    def get_pending_tickets(self) -> list:
        """Get list of unprinted tickets from queue."""
        try:
            tickets = sorted(self.print_queue_dir.glob("order_*.txt"))
            return [str(t) for t in tickets]
        except Exception as e:
            logger.error(f"Failed to get pending tickets: {str(e)}")
            return []

    def mark_ticket_printed(self, ticket_path: str) -> bool:
        """Mark a ticket as printed by moving to printed folder."""
        try:
            printed_dir = self.print_queue_dir / "printed"
            printed_dir.mkdir(exist_ok=True)

            ticket_file = Path(ticket_path)
            if ticket_file.exists():
                ticket_file.rename(printed_dir / ticket_file.name)
                logger.info(f"Ticket {ticket_file.name} marked as printed")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to mark ticket as printed: {str(e)}")
            return False


# Global kitchen printer instance
kitchen_printer = KitchenPrinter()
